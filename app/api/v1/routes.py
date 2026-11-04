"""FastAPI v1 endpoints for document ingestion, retrieval, and generation."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import Settings, get_settings
from app.generation.llm import get_llm
from app.generation.prompts import PromptBuilder
from app.indexing.chunker import SentenceTokenChunker
from app.indexing.embedder import get_embedder
from app.indexing.vector_store import DualVectorStore
from app.ingestion.cleaner import TextCleaner
from app.ingestion.parsers import DocumentParser
from app.ingestion.registry import DocumentRegistry
from app.models.schemas import (
    DocumentRecord,
    DocumentStatus,
    EvalRunRecord,
    GoldenItem,
    QueryRequest,
    QueryResponse,
    RetrievedPassage,
    TimingBreakdown,
)
from app.retrieval.advanced import AdvancedRetriever
from app.retrieval.bm25 import BM25Index
from app.retrieval.retriever import KNNRetriever
from app.utils.logging import get_logger

logger = get_logger("api_v1")
router = APIRouter(prefix="/v1")


class PipelineServices:
    """Dependency container for RAG pipeline components."""

    def __init__(self, settings: Settings) -> None:
        """Initialize all pipeline singletons."""
        self.settings = settings
        self.registry = DocumentRegistry(config=settings.ingestion)
        self.parser = DocumentParser()
        self.cleaner = TextCleaner(config=settings.cleaner)
        self.chunker = SentenceTokenChunker(config=settings.chunking)
        self.embedder = get_embedder(config=settings.embedding)
        self.vector_store = DualVectorStore(
            dimension=self.embedder.dimension,
            config=settings.indexing,
        )
        self.bm25_index = BM25Index(k1=1.5, b=0.75)
        self.dense_retriever = KNNRetriever(
            vector_index=self.vector_store,
            embedder=self.embedder,
            config=settings.retrieval,
        )
        self.prompt_builder = PromptBuilder(config=settings.generation)
        self.llm = get_llm(config=settings.generation)

        # Hydrate BM25 from existing vector store chunks
        existing_chunks = self.vector_store.get_all_chunks()
        if existing_chunks:
            self.bm25_index.index_chunks(existing_chunks)

        self.retriever = AdvancedRetriever(
            dense_retriever=self.dense_retriever,
            bm25_index=self.bm25_index,
            llm=self.llm,
            config=settings.retrieval,
        )

        # Golden dataset manager
        from app.eval.golden import GoldenDatasetManager

        self.golden_manager = GoldenDatasetManager(
            storage_dir=settings.eval.golden_set_dir
        )
        self.golden_manager.load_from_file("golden_v1.jsonl")


_SERVICES: PipelineServices | None = None


def get_services() -> PipelineServices:
    """Retrieve global cached pipeline services."""
    global _SERVICES
    if _SERVICES is None:
        _SERVICES = PipelineServices(get_settings())
    return _SERVICES


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(
    services: PipelineServices = Depends(get_services),
) -> dict[str, Any]:
    """Liveness check and system health metrics."""
    return {
        "status": "healthy",
        "app": services.settings.app.name,
        "version": services.settings.app.version,
        "indexed_chunks": services.vector_store.count(),
    }


@router.post("/documents", response_model=DocumentRecord)
def upload_document(
    file: UploadFile = File(...),
    services: PipelineServices = Depends(get_services),
) -> DocumentRecord:
    """Upload and ingest a document into the RAG pipeline."""
    filename = file.filename or "uploaded_file"
    file_bytes = file.file.read()
    mime = file.content_type or ""

    # 1. Validate and register in SQLite
    try:
        record, is_new = services.registry.register_document(
            filename=filename,
            file_bytes=file_bytes,
            mime=mime,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # If already parsed and ready, return existing record
    if not is_new and record.status == DocumentStatus.READY:
        return record

    try:
        # 2. Parse file bytes
        services.registry.update_status(record.doc_id, DocumentStatus.PARSING)
        parsed = services.parser.parse(
            file_bytes=file_bytes,
            filename=filename,
            mime=mime,
            checksum=record.checksum,
        )

        # 3. Clean parsed text
        cleaned = services.cleaner.clean_document(parsed)

        # 4. Chunk document
        services.registry.update_status(record.doc_id, DocumentStatus.INDEXING)
        config_hash = services.settings.get_config_hash()
        chunks = services.chunker.chunk(
            doc=cleaned,
            embedding_model=services.embedder.model_name,
            config_hash=config_hash,
        )

        # 5. Embed and Index chunks
        if chunks:
            texts = [c.text for c in chunks]
            embeddings = services.embedder.embed_texts(texts)
            services.vector_store.add(chunks, embeddings)
            services.bm25_index.index_chunks(chunks)

        # 6. Mark ready
        services.registry.update_status(
            doc_id=record.doc_id,
            status=DocumentStatus.READY,
            pages=cleaned.total_pages,
        )
        updated = services.registry.get_by_doc_id(record.doc_id)
        if updated:
            return updated
        return record
    except Exception as e:
        logger.error("Document ingestion failed", doc_id=record.doc_id, error=str(e))
        services.registry.update_status(
            doc_id=record.doc_id,
            status=DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {e}",
        ) from e


@router.get("/documents", response_model=list[DocumentRecord])
def list_documents(
    services: PipelineServices = Depends(get_services),
) -> list[DocumentRecord]:
    """List all registered documents."""
    return services.registry.list_documents()


@router.delete("/documents/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(
    doc_id: str,
    services: PipelineServices = Depends(get_services),
) -> dict[str, Any]:
    """Delete document from database, disk storage, and vector index."""
    # Delete from vector store (Chroma + FAISS)
    deleted_vectors = services.vector_store.delete_by_doc_id(doc_id)
    services.bm25_index.delete_by_doc_id(doc_id)

    # Delete from SQLite registry & raw storage
    deleted_db = services.registry.delete_document(doc_id)
    if not deleted_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id '{doc_id}' not found.",
        )

    return {
        "status": "deleted",
        "doc_id": doc_id,
        "deleted_chunks": deleted_vectors,
    }


@router.get("/documents/{doc_id}/download")
def download_document(
    doc_id: str,
    services: PipelineServices = Depends(get_services),
) -> FileResponse:
    """Download the raw manuscript file for the given doc_id."""
    doc = services.registry.get_by_doc_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id '{doc_id}' not found.",
        )

    file_path = services.registry.get_raw_file_path(doc_id)
    if not file_path or not file_path.exists():
        # Fallback: synthesize plain text file from vector store chunks
        chunks = [
            c for c in services.vector_store.get_all_chunks() if c.doc_id == doc_id
        ]
        if chunks:
            chunks.sort(key=lambda c: c.idx)
            text_content = "\n\n".join(c.text for c in chunks)
            temp_path = (
                services.registry.raw_dir / "uploads" / f"{doc_id}_{doc.filename}"
            )
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(text_content, encoding="utf-8")
            file_path = temp_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Raw manuscript file for '{doc.filename}' could not be located.",
            )

    return FileResponse(
        path=file_path,
        filename=doc.filename,
        media_type=doc.mime or "application/octet-stream",
    )


@router.get("/documents/{doc_id}/preview")
def preview_document(
    doc_id: str,
    services: PipelineServices = Depends(get_services),
) -> dict[str, Any]:
    """Retrieve full text and metadata preview for a document."""
    doc = services.registry.get_by_doc_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id '{doc_id}' not found.",
        )

    chunks = [
        c for c in services.vector_store.get_all_chunks() if c.doc_id == doc_id
    ]
    chunks.sort(key=lambda c: c.idx)
    preview_text = "\n\n".join(c.text for c in chunks)

    return {
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "pages": doc.pages,
        "mime": doc.mime,
        "checksum": doc.checksum,
        "uploaded_at": doc.uploaded_at.isoformat(),
        "status": doc.status.value,
        "chunks_count": len(chunks),
        "preview_text": preview_text or "No text content indexed.",
    }


@router.post("/retrieve", response_model=list[RetrievedPassage])
def retrieve_passages(
    payload: QueryRequest,
    services: PipelineServices = Depends(get_services),
) -> list[RetrievedPassage]:
    """Debug retrieval endpoint returning top-k matching passages."""
    return services.retriever.retrieve(
        query=payload.question,
        top_k=payload.k,
        filters=payload.filters,
        hybrid_enabled=payload.hybrid_enabled,
        reranker_enabled=payload.reranker_enabled,
        query_transform_strategy=payload.query_transform_strategy,
    )


@router.post("/query", response_model=QueryResponse)
def query_qa(
    payload: QueryRequest,
    services: PipelineServices = Depends(get_services),
) -> QueryResponse:
    """Execute end-to-end question answering over indexed documents."""
    trace_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    # 1. Retrieval stage
    t_ret_start = time.perf_counter()
    passages = services.retriever.retrieve(
        query=payload.question,
        top_k=payload.k,
        filters=payload.filters,
        hybrid_enabled=payload.hybrid_enabled,
        reranker_enabled=payload.reranker_enabled,
        query_transform_strategy=payload.query_transform_strategy,
    )
    t_ret_end = time.perf_counter()
    retrieval_ms = (t_ret_end - t_ret_start) * 1000.0

    # 2. Build prompt
    system_prompt = services.prompt_builder.build_system_prompt()
    user_prompt = services.prompt_builder.build_user_prompt(
        question=payload.question,
        passages=passages,
    )

    # 3. Generation stage
    t_gen_start = time.perf_counter()
    raw_answer = services.llm.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
    )
    t_gen_end = time.perf_counter()
    generation_ms = (t_gen_end - t_gen_start) * 1000.0

    total_ms = (time.perf_counter() - t0) * 1000.0

    # 4. Extract citations and check abstention
    abstained = services.prompt_builder.is_abstained(raw_answer)
    doc_map = {d.doc_id: d.filename for d in services.registry.list_documents()}
    citations = (
        []
        if abstained
        else services.prompt_builder.extract_citations(raw_answer, passages, doc_map)
    )

    return QueryResponse(
        answer=raw_answer,
        citations=citations,
        contexts=passages,
        timings=TimingBreakdown(
            retrieval_ms=round(retrieval_ms, 2),
            generation_ms=round(generation_ms, 2),
            total_ms=round(total_ms, 2),
        ),
        trace_id=trace_id,
        abstained=abstained,
    )


def generate_sse_stream(
    payload: QueryRequest,
    services: PipelineServices,
) -> Iterator[str]:
    """Generate Server-Sent Event formatted chunks for query response."""
    trace_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    # 1. Retrieval
    t_ret_start = time.perf_counter()
    passages = services.retriever.retrieve(
        query=payload.question,
        top_k=payload.k,
        filters=payload.filters,
        hybrid_enabled=payload.hybrid_enabled,
        reranker_enabled=payload.reranker_enabled,
        query_transform_strategy=payload.query_transform_strategy,
    )
    retrieval_ms = (time.perf_counter() - t_ret_start) * 1000.0

    # 2. Build prompt
    system_prompt = services.prompt_builder.build_system_prompt()
    user_prompt = services.prompt_builder.build_user_prompt(
        question=payload.question,
        passages=passages,
    )

    full_tokens: list[str] = []
    t_gen_start = time.perf_counter()

    # Stream generated tokens
    for token in services.llm.generate_stream(
        prompt=user_prompt,
        system_prompt=system_prompt,
    ):
        full_tokens.append(token)
        data = json.dumps({"token": token, "trace_id": trace_id})
        yield f"data: {data}\n\n"

    generation_ms = (time.perf_counter() - t_gen_start) * 1000.0
    total_ms = (time.perf_counter() - t0) * 1000.0
    full_answer = "".join(full_tokens)

    # Citations & metadata event
    abstained = services.prompt_builder.is_abstained(full_answer)
    doc_map = {d.doc_id: d.filename for d in services.registry.list_documents()}
    citations = (
        []
        if abstained
        else services.prompt_builder.extract_citations(full_answer, passages, doc_map)
    )

    final_payload = {
        "done": True,
        "answer": full_answer,
        "citations": [c.model_dump() for c in citations],
        "contexts": [p.model_dump() for p in passages],
        "timings": {
            "retrieval_ms": round(retrieval_ms, 2),
            "generation_ms": round(generation_ms, 2),
            "total_ms": round(total_ms, 2),
        },
        "abstained": abstained,
        "trace_id": trace_id,
    }
    yield f"data: {json.dumps(final_payload)}\n\n"


@router.post("/query/stream")
def query_stream(
    payload: QueryRequest,
    services: PipelineServices = Depends(get_services),
) -> StreamingResponse:
    """Stream answer tokens over Server-Sent Events (SSE)."""
    return StreamingResponse(
        generate_sse_stream(payload, services),
        media_type="text/event-stream",
    )


# ==========================================
# Phase 4: Golden Dataset & Evaluation APIs
# ==========================================


@router.get("/golden", response_model=list[GoldenItem])
def list_golden_items(
    split: str | None = None,
    q_type: str | None = None,
    services: PipelineServices = Depends(get_services),
) -> list[GoldenItem]:
    """Retrieve filtered golden QA benchmark items."""
    return services.golden_manager.list_items(split=split, q_type=q_type)


@router.post(
    "/golden",
    response_model=GoldenItem,
    status_code=status.HTTP_201_CREATED,
)
def add_golden_item(
    item: GoldenItem,
    services: PipelineServices = Depends(get_services),
) -> GoldenItem:
    """Register or update a golden QA benchmark item."""
    services.golden_manager.add_item(item)
    services.golden_manager.save_to_file("golden_v1.jsonl")
    return item


@router.post("/eval/run")
def trigger_eval_run(
    split: str = "train",
    top_k: int = 5,
    services: PipelineServices = Depends(get_services),
) -> dict[str, Any]:
    """Trigger a quantitative evaluation benchmark over the golden dataset."""
    from app.eval.runner import BenchmarkRunner

    runner = BenchmarkRunner(
        services=services,
        golden_manager=services.golden_manager,
    )
    summary = runner.run_benchmark(split=split, top_k=top_k)
    runner.export_reports(summary)
    record = runner.save_run_record(summary)
    return {
        "run_id": summary.run_id,
        "config_hash": summary.config_hash,
        "split": summary.split,
        "item_count": summary.item_count,
        "metrics": summary.metrics.model_dump(),
        "latency_p50_ms": summary.latency_p50_ms,
        "latency_p95_ms": summary.latency_p95_ms,
        "record": record.model_dump(),
    }


@router.get("/eval/runs", response_model=list[EvalRunRecord])
def list_eval_runs() -> list[EvalRunRecord]:
    """List historical evaluation benchmark run records."""
    from pathlib import Path

    runs_file = Path("data/eval_runs.jsonl")
    if not runs_file.exists():
        return []
    records: list[EvalRunRecord] = []
    with open(runs_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(EvalRunRecord(**json.loads(line.strip())))
    return records
