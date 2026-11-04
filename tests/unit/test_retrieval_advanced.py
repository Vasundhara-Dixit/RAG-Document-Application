"""Unit tests for Phase 6 advanced retrieval features: ParentRetriever, Hierarchical chunking, and QueryProcessor."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.core.config import ChunkingConfig
from app.core.interfaces import LLM, Retriever
from app.indexing.chunker import SentenceTokenChunker
from app.models.schemas import ChunkRecord, ParsedDocument, ParsedPage, RetrievedPassage
from app.retrieval.parent_retriever import ParentDocumentRetriever
from app.retrieval.transforms import QueryProcessor


def _make_parsed_doc(text: str) -> ParsedDocument:
    return ParsedDocument(
        doc_id="test_doc",
        filename="test_manual.txt",
        mime="text/plain",
        checksum="dummyhash",
        pages=[ParsedPage(page_number=1, text=text, char_offset_start=0, char_offset_end=len(text))],
        total_pages=1,
    )


class DummyLLM(LLM):
    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        self.mapping = mapping or {}

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        for k, v in self.mapping.items():
            if k in prompt:
                return v
        return "Hypothetical technical document text discussing specifications and policies."

    def generate_stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        yield self.generate(prompt)


class DummyRetriever(Retriever):
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


def test_contextual_enrichment() -> None:
    config = ChunkingConfig(chunk_size=100, chunk_overlap=10, contextual_enrichment=True)
    chunker = SentenceTokenChunker(config=config)
    doc = _make_parsed_doc("# 1. Security Overview\nAll systems require multi-factor authentication (MFA).")
    chunks = chunker.chunk(doc, embedding_model="test-embedder", config_hash="hash1")

    assert len(chunks) == 1
    assert "[Document: test_manual.txt | Section: 1. Security Overview]" in chunks[0].text
    assert "MFA" in chunks[0].text


def test_hierarchical_chunking() -> None:
    config = ChunkingConfig(chunk_size=50, child_chunk_size=20, chunk_overlap=5)
    chunker = SentenceTokenChunker(config=config)
    long_text = (
        "First sentence of the security policy. Second sentence detailing token requirements. "
        "Third sentence outlining backup retention windows. Fourth sentence on incident management."
    )
    doc = _make_parsed_doc(long_text)
    parents, children = chunker.chunk_hierarchical(doc, embedding_model="test", config_hash="hash")

    assert len(parents) >= 1
    assert len(children) >= 1
    # Verify child chunks link to a parent chunk
    parent_ids = {p.chunk_id for p in parents}
    for c in children:
        assert c.parent_id in parent_ids


def test_parent_document_retriever() -> None:
    parent = ChunkRecord(
        chunk_id="parent_01",
        doc_id="doc1",
        idx=0,
        text="Full comprehensive parent context spanning multiple paragraphs.",
        token_count=100,
        page_start=1,
        page_end=1,
        char_start=0,
        char_end=200,
        embedding_model="test",
        config_hash="h",
    )
    child = ChunkRecord(
        chunk_id="child_01",
        doc_id="doc1",
        idx=0,
        text="Short child snippet.",
        token_count=20,
        page_start=1,
        page_end=1,
        char_start=0,
        char_end=20,
        parent_id="parent_01",
        embedding_model="test",
        config_hash="h",
    )

    child_retriever = DummyRetriever([RetrievedPassage(chunk=child, score=0.95)])
    parent_retriever = ParentDocumentRetriever(child_retriever=child_retriever)
    parent_retriever.register_parents([parent])

    results = parent_retriever.retrieve("What is in the manual?", top_k=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "parent_01"
    assert "Full comprehensive parent context" in results[0].chunk.text


def test_query_processor_hyde_and_multi_query() -> None:
    llm = DummyLLM(
        {
            "Write a concise": "Acme Corporation uses AES-256 for all secondary backups.",
            "Generate 3 alternative": "encryption standards for backups\nbackup archive cipher policy\nAES-256 backup rules",
            "step-back": "What is the general data backup and encryption architecture?",
        }
    )
    qp = QueryProcessor(llm=llm)

    # HyDE
    hyde_doc = qp.generate_hyde("What cipher is used?")
    assert "AES-256" in hyde_doc

    # Multi-query
    mq = qp.generate_multi_query("What cipher is used?", num_variants=3)
    assert len(mq) >= 2
    assert "What cipher is used?" in mq

    # Step-back
    sb = qp.generate_step_back("What cipher is used?")
    assert "general data backup" in sb

