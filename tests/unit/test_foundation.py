"""Unit tests for Phase 0 Foundation components."""

from app.core.config import load_config
from app.models.schemas import (
    ChunkRecord,
    Citation,
    DocumentRecord,
    DocumentStatus,
    GoldenItem,
    GoldenQuestionType,
    GoldenSplit,
    QueryResponse,
    RetrievedPassage,
    TimingBreakdown,
)
from app.utils.logging import get_logger, setup_logging


def test_load_default_config() -> None:
    """Verify that configs/config.yaml loads with valid schema and defaults."""
    settings = load_config("configs/config.yaml")
    assert settings.app.name == "RAG Document Q&A"
    assert settings.chunking.chunk_size == 512
    assert settings.chunking.chunk_overlap == 51
    assert settings.indexing.index_type == "IndexFlatIP"
    assert settings.retrieval.default_k == 5
    assert len(settings.ingestion.allowed_extensions) == 4
    assert ".pdf" in settings.ingestion.allowed_extensions


def test_config_hash_determinism() -> None:
    """Verify that config hash is deterministic and sensitive to chunking/embedding."""
    settings = load_config("configs/config.yaml")
    hash1 = settings.get_config_hash()
    hash2 = settings.get_config_hash()
    assert hash1 == hash2
    assert len(hash1) == 16

    # Modify chunk size and verify hash changes
    mutated = settings.model_copy(deep=True)
    mutated.chunking.chunk_size = 256
    assert mutated.get_config_hash() != hash1


def test_schemas_instantiation() -> None:
    """Verify data schemas instantiation, validation, and serialization."""
    doc = DocumentRecord(
        doc_id="test_doc_123",
        filename="report.pdf",
        mime="application/pdf",
        pages=3,
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status=DocumentStatus.READY,
    )
    assert doc.doc_id == "test_doc_123"
    assert doc.status == DocumentStatus.READY

    chunk = ChunkRecord(
        chunk_id="chk_001",
        doc_id="test_doc_123",
        idx=0,
        text="Sample passage text.",
        token_count=4,
        page_start=1,
        page_end=1,
        char_start=0,
        char_end=20,
        embedding_model="text-embedding-3-small",
        config_hash="abc123hash",
    )
    assert chunk.chunk_id == "chk_001"

    passage = RetrievedPassage(chunk=chunk, score=0.92)
    assert passage.score == 0.92

    resp = QueryResponse(
        answer="This is the answer.",
        citations=[
            Citation(
                citation_index=1,
                doc_id=doc.doc_id,
                filename=doc.filename,
                page=1,
                snippet="Sample passage text.",
                chunk_id=chunk.chunk_id,
            )
        ],
        contexts=[passage],
        timings=TimingBreakdown(retrieval_ms=45.2, generation_ms=350.1, total_ms=395.3),
        trace_id="trace_001",
        abstained=False,
    )
    assert len(resp.citations) == 1
    assert resp.timings.total_ms == 395.3


def test_golden_item_schema() -> None:
    """Verify GoldenItem schema fields and enum validation."""
    item = GoldenItem(
        id="golden_001",
        question="What is the RTO target?",
        reference_answer="15 minutes",
        doc_id="doc_ops_manual",
        chunk_ids=["chk_002"],
        page=2,
        type=GoldenQuestionType.NUMERIC,
        split=GoldenSplit.TRAIN,
    )
    assert item.type == GoldenQuestionType.NUMERIC
    assert item.split == GoldenSplit.TRAIN


def test_logging_setup() -> None:
    """Verify logger setup runs without errors."""
    setup_logging("DEBUG")
    logger = get_logger("test_logger")
    logger.debug("Test debug message", test_key="test_value")
