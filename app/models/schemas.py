"""Pydantic data models and schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    """Document processing state."""

    QUEUED = "queued"
    PARSING = "parsing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class DocumentRecord(BaseModel):
    """Document metadata stored in SQLite registry."""

    doc_id: str
    filename: str
    mime: str
    pages: int = 1
    checksum: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: DocumentStatus = DocumentStatus.QUEUED
    error_message: str | None = None
    tags: list[str] = Field(default_factory=list)


class ChunkRecord(BaseModel):
    """Individual text chunk with exact provenance and indexing metadata."""

    chunk_id: str
    doc_id: str
    idx: int
    text: str
    token_count: int
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    section_title: str | None = None
    parent_id: str | None = None
    embedding_model: str
    config_hash: str


class ParsedPage(BaseModel):
    """Single page extracted during document parsing."""

    page_number: int
    text: str
    char_offset_start: int = 0
    char_offset_end: int = 0


class ParsedDocument(BaseModel):
    """Full parsed representation of an uploaded file."""

    doc_id: str
    filename: str
    mime: str
    checksum: str
    pages: list[ParsedPage]
    total_pages: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Citation pointing to a specific source passage."""

    citation_index: int = 1
    doc_id: str
    filename: str
    page: int
    snippet: str
    chunk_id: str


class RetrievedPassage(BaseModel):
    """Retrieved chunk with relevance score."""

    chunk: ChunkRecord
    score: float


class QueryRequest(BaseModel):
    """Request payload for /v1/query."""

    question: str
    k: int | None = None
    filters: dict[str, Any] | None = None
    conv_id: str | None = None
    hybrid_enabled: bool | None = None
    reranker_enabled: bool | None = None
    query_transform_strategy: str | None = None


class TimingBreakdown(BaseModel):
    """Latency breakdown across pipeline stages in milliseconds."""

    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0


class QueryResponse(BaseModel):
    """Standardized response schema for Q&A queries."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    contexts: list[RetrievedPassage] = Field(default_factory=list)
    timings: TimingBreakdown = Field(default_factory=TimingBreakdown)
    trace_id: str
    abstained: bool = False


class GoldenSplit(StrEnum):
    """Split partition for Golden set items."""

    TRAIN = "train"
    HOLDOUT = "holdout"


class GoldenQuestionType(StrEnum):
    """Taxonomy of golden test questions."""

    FACTOID = "factoid"
    NUMERIC = "numeric"
    MULTI_SENTENCE = "multi_sentence"
    NO_ANSWER = "no_answer"
    AMBIGUOUS = "ambiguous"


class GoldenItem(BaseModel):
    """Golden QA item for retrieval and generation benchmarks."""

    id: str
    question: str
    reference_answer: str
    doc_id: str
    chunk_ids: list[str] = Field(default_factory=list)
    page: int
    type: GoldenQuestionType = GoldenQuestionType.FACTOID
    split: GoldenSplit = GoldenSplit.TRAIN
    version: str = "v1.0"


class EvalMetrics(BaseModel):
    """Quantitative benchmark results."""

    hit_at_1: float = 0.0
    hit_at_3: float = 0.0
    hit_at_5: float = 0.0
    hit_at_10: float = 0.0
    mrr: float = 0.0
    faithfulness: float | None = None
    correctness: float | None = None
    completeness: float | None = None


class EvalRunRecord(BaseModel):
    """Persisted record of an evaluation benchmark run."""

    run_id: str
    config_hash: str
    dataset_version: str
    metrics: EvalMetrics
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    git_sha: str | None = None
    notes: str | None = None
