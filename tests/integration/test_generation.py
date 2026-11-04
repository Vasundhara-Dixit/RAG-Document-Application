"""Integration tests for FastAPI endpoints: retrieval, generation, streaming."""

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.api.v1.routes import (
    PipelineServices,
    delete_document,
    download_document,
    generate_sse_stream,
    health_check,
    preview_document,
    query_qa,
    query_stream,
    retrieve_passages,
    upload_document,
)
from app.core.config import get_settings
from app.models.schemas import QueryRequest


@pytest.fixture
def isolated_services(tmp_path: Path) -> PipelineServices:
    """Create isolated pipeline services within a temporary directory."""
    settings = get_settings().model_copy(deep=True)
    settings.ingestion.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    settings.ingestion.raw_data_dir = str(tmp_path / "raw")
    settings.indexing.chroma_persist_dir = str(tmp_path / "chroma")
    settings.indexing.faiss_index_path = str(tmp_path / "faiss.index")
    return PipelineServices(settings)


def test_health_endpoint(isolated_services: PipelineServices) -> None:
    """Verify health check returns status and zero or positive indexed count."""
    res = health_check(services=isolated_services)
    assert res["status"] == "healthy"
    assert "indexed_chunks" in res
    assert res["indexed_chunks"] == 0


def test_full_rag_pipeline_flow(
    isolated_services: PipelineServices,
) -> None:
    """Verify upload, retrieval, grounded generation, streaming, and deletion."""
    sample_path = Path("tests/fixtures/sample.txt")
    raw_bytes = sample_path.read_bytes()

    # 1. Upload and ingest document
    mock_upload = MagicMock()
    mock_upload.filename = "sample.txt"
    mock_upload.content_type = "text/plain"
    mock_upload.file = io.BytesIO(raw_bytes)

    doc_record = upload_document(
        file=mock_upload,
        services=isolated_services,
    )
    assert doc_record.filename == "sample.txt"
    assert doc_record.status.value == "ready"
    assert doc_record.pages >= 1

    # 2. Debug retrieval
    ret_passages = retrieve_passages(
        QueryRequest(
            question="What are the backup procedures and retention policy?",
            k=3,
        ),
        services=isolated_services,
    )
    assert len(ret_passages) >= 1
    assert ret_passages[0].chunk.doc_id == doc_record.doc_id

    # 2b. Preview and Download endpoints
    preview_res = preview_document(doc_record.doc_id, services=isolated_services)
    assert preview_res["doc_id"] == doc_record.doc_id
    assert preview_res["filename"] == "sample.txt"
    assert preview_res["chunks_count"] >= 1
    assert len(preview_res["preview_text"]) > 0

    download_res = download_document(doc_record.doc_id, services=isolated_services)
    assert download_res.status_code == 200
    assert Path(download_res.path) == isolated_services.registry.get_raw_file_path(doc_record.doc_id)

    # 3. Grounded Q&A query
    qa_resp = query_qa(
        QueryRequest(
            question="When do nightly backups execute and what is the retention?",
            k=3,
        ),
        services=isolated_services,
    )
    assert qa_resp.abstained is False
    assert "02:00 UTC" in qa_resp.answer or "backups" in qa_resp.answer.lower()
    assert len(qa_resp.citations) >= 1
    assert qa_resp.citations[0].filename == "sample.txt"
    assert qa_resp.timings.total_ms > 0
    assert len(qa_resp.trace_id) > 0

    # 3b. General overview query should NOT abstain
    overview_resp = query_qa(
        QueryRequest(
            question="what is this about",
            k=3,
        ),
        services=isolated_services,
    )
    assert overview_resp.abstained is False
    assert len(overview_resp.answer) > 20
    assert len(overview_resp.citations) >= 1

    # 4. Out-of-domain query (Abstention verification)
    abstain_resp = query_qa(
        QueryRequest(
            question="What is the capital city of Mars?",
            k=3,
        ),
        services=isolated_services,
    )
    assert abstain_resp.abstained is True
    assert (
        "don't contain enough information" in abstain_resp.answer.lower()
        or "do not contain enough information" in abstain_resp.answer.lower()
    )
    assert len(abstain_resp.citations) == 0

    # 5. SSE Streaming response
    stream_response = query_stream(
        QueryRequest(
            question="What is the backup retention policy?",
            k=2,
        ),
        services=isolated_services,
    )
    assert stream_response.media_type == "text/event-stream"

    # Verify event stream generator
    stream_chunks = list(
        generate_sse_stream(
            QueryRequest(
                question="What is the backup retention policy?",
                k=2,
            ),
            isolated_services,
        )
    )
    full_stream = "".join(stream_chunks)
    assert "data: " in full_stream
    assert '"done": true' in full_stream

    # 6. Delete document
    del_result = delete_document(
        doc_id=doc_record.doc_id,
        services=isolated_services,
    )
    assert del_result["status"] == "deleted"
    assert del_result["doc_id"] == doc_record.doc_id
    assert isolated_services.vector_store.count() == 0
