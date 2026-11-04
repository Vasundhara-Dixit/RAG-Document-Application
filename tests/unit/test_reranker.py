"""Unit tests for FastCrossEncoderReranker and LLMCrossEncoderReranker."""

from __future__ import annotations

from collections.abc import Iterator

from app.core.interfaces import LLM
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.retrieval.reranker import (
    FastCrossEncoderReranker,
    LLMCrossEncoderReranker,
    get_reranker,
)


def _make_passage(chunk_id: str, text: str, base_score: float) -> RetrievedPassage:
    chunk = ChunkRecord(
        chunk_id=chunk_id,
        doc_id="test_doc",
        idx=0,
        text=text,
        token_count=len(text.split()),
        page_start=1,
        page_end=1,
        char_start=0,
        char_end=len(text),
        embedding_model="test-model",
        config_hash="testhash",
    )
    return RetrievedPassage(chunk=chunk, score=base_score)


class DummyLLM(LLM):
    def __init__(self, score_to_return: str) -> None:
        self.score_to_return = score_to_return

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return self.score_to_return

    def generate_stream(
        self, prompt: str, system_prompt: str | None = None
    ) -> Iterator[str]:
        yield self.score_to_return


def test_fast_reranker_reordering() -> None:
    # Query is about encryption algorithm for backups
    query = "What encryption algorithm is used for backup archives?"

    # Passage 1 has high base score from dense embedder but talks generally about cloud operations
    p1 = _make_passage("p1", "The Acme Cloud Platform runs across 3 availability zones.", 0.85)

    # Passage 2 has lower base score but exact match on encryption algorithm and backup archives
    p2 = _make_passage(
        "p2",
        "All database and filesystem backup archives are strictly encrypted using AES-256-GCM algorithms.",
        0.65,
    )

    reranker = FastCrossEncoderReranker()
    reranked = reranker.rerank(query, [p1, p2], top_k=2)

    assert len(reranked) == 2
    # p2 should be elevated to top rank because of phrase match, coverage, and proximity
    assert reranked[0].chunk.chunk_id == "p2"
    assert reranked[0].score > reranked[1].score


def test_fast_reranker_empty_inputs() -> None:
    reranker = FastCrossEncoderReranker()
    assert reranker.rerank("", [_make_passage("p1", "hello", 0.5)], 1) == []
    assert reranker.rerank("query", [], 1) == []


def test_llm_reranker() -> None:
    llm = DummyLLM("9")
    reranker = LLMCrossEncoderReranker(llm=llm)
    p = _make_passage("p1", "Relevant text", 0.5)
    reranked = reranker.rerank("test query", [p], top_k=1)
    assert len(reranked) == 1
    assert reranked[0].score == 0.9


def test_get_reranker_factory() -> None:
    r_fast = get_reranker("fast")
    assert isinstance(r_fast, FastCrossEncoderReranker)

    r_llm = get_reranker("llm", llm=DummyLLM("8"))
    assert isinstance(r_llm, LLMCrossEncoderReranker)

