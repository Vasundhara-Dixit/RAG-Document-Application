"""Unit tests for Okapi BM25 index and HybridRetriever with RRF."""

from __future__ import annotations

from typing import Any

from app.core.interfaces import Retriever
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.retrieval.bm25 import BM25Index, tokenize_bm25
from app.retrieval.hybrid import HybridRetriever


def _make_chunk(chunk_id: str, doc_id: str, text: str, page: int = 1) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        doc_id=doc_id,
        idx=0,
        text=text,
        token_count=len(text.split()),
        page_start=page,
        page_end=page,
        char_start=0,
        char_end=len(text),
        embedding_model="test-embedder",
        config_hash="testhash",
    )


class DummyDenseRetriever(Retriever):
    """Mock retriever returning canned passages."""

    def __init__(self, passages: list[RetrievedPassage]) -> None:
        self.passages = passages

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        k = top_k or len(self.passages)
        return self.passages[:k]


def test_tokenize_bm25() -> None:
    tokens = tokenize_bm25("Acme's Cloud Platform, v2.0 (TLS 1.3)!")
    assert "acme" in tokens
    assert "cloud" in tokens
    assert "platform" in tokens
    assert "tls" in tokens


def test_bm25_index_and_search() -> None:
    index = BM25Index(k1=1.5, b=0.75)
    c1 = _make_chunk("c1", "doc1", "The quick brown fox jumps over the lazy dog.")
    c2 = _make_chunk("c2", "doc2", "Database backups run nightly using AES-256 encryption.")
    c3 = _make_chunk("c3", "doc2", "Incident response team uses PagerDuty and Slack alerts.")

    index.index_chunks([c1, c2, c3])
    assert index.count() == 3

    # Search for encryption
    results = index.search("AES-256 encryption", top_k=5)
    assert len(results) > 0
    assert results[0][0].chunk_id == "c2"

    # Search with doc_id filter
    filtered = index.search("backups", filters={"doc_id": "doc1"})
    assert len(filtered) == 0

    # Delete doc2
    deleted = index.delete_by_doc_id("doc2")
    assert deleted == 2
    assert index.count() == 1
    assert len(index.search("backups")) == 0


def test_hybrid_rrf_scoring_and_ranking() -> None:
    c1 = _make_chunk("c1", "doc1", "Encryption standard AES-256 for backups")
    c2 = _make_chunk("c2", "doc2", "Incident management escalation matrix")
    c3 = _make_chunk("c3", "doc3", "Quarterly financial statement revenue")

    # Dense ranks: c1 (rank 1), c2 (rank 2)
    dense_passages = [
        RetrievedPassage(chunk=c1, score=0.9),
        RetrievedPassage(chunk=c2, score=0.8),
    ]
    dense_retriever = DummyDenseRetriever(dense_passages)

    # BM25: index c1, c2, c3
    bm25_index = BM25Index()
    bm25_index.index_chunks([c1, c2, c3])

    hybrid = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_index=bm25_index,
        rrf_k=60,
    )

    # Query matching c3 specifically on keywords
    results = hybrid.retrieve("Quarterly financial revenue", top_k=3)
    assert len(results) <= 3

    # Hand-calculate RRF:
    # c3 is rank 1 in BM25: 1/(60+1) = 0.016393
    # c1 is rank 1 in dense (0.016393)
    # c2 is rank 2 in dense (1/(60+2) = 0.016129)
    result_ids = [p.chunk.chunk_id for p in results]
    assert "c3" in result_ids
    assert "c1" in result_ids

