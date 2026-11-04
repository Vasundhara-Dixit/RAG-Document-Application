"""Abstract base interfaces for pluggable pipeline stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from app.models.schemas import (
    ChunkRecord,
    ParsedDocument,
    RetrievedPassage,
)


class Parser(ABC):
    """Abstract interface for file-format specific document parsers."""

    @abstractmethod
    def can_parse(self, filename: str, mime: str) -> bool:
        """Check if parser handles given file extension or MIME type."""
        ...

    @abstractmethod
    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str,
        checksum: str,
    ) -> ParsedDocument:
        """Extract text and per-page structures from file bytes."""
        ...


class Cleaner(ABC):
    """Abstract interface for text normalization and sanitization."""

    @abstractmethod
    def clean_text(self, text: str) -> str:
        """Clean single string (de-hyphenate, strip whitespace, unicode normalize)."""
        ...

    @abstractmethod
    def clean_document(self, doc: ParsedDocument) -> ParsedDocument:
        """Apply cleaning to all pages in parsed document."""
        ...


class Chunker(ABC):
    """Abstract interface for document chunking algorithms."""

    @abstractmethod
    def chunk(
        self,
        doc: ParsedDocument,
        embedding_model: str,
        config_hash: str,
    ) -> list[ChunkRecord]:
        """Split parsed document into token-bounded, sentence-aware chunks."""
        ...


class Embedder(ABC):
    """Abstract interface for dense embedding generation."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying embedding model."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimensionality."""
        ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embeddings for a batch of strings."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Generate normalized embedding for a single search query."""
        ...


class VectorIndex(ABC):
    """Abstract interface for vector similarity search and storage."""

    @abstractmethod
    def add(
        self,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
    ) -> None:
        """Index a batch of chunks with corresponding vector embeddings."""
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Search nearest chunks by vector similarity."""
        ...

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> int:
        """Remove all chunks associated with a specific document ID."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Total number of indexed vectors."""
        ...

    @abstractmethod
    def save(self) -> None:
        """Persist index state to disk."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Load index state from disk."""
        ...


class Retriever(ABC):
    """Abstract interface for passage retrieval orchestrators."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Retrieve most relevant passages for a natural language query."""
        ...


class Reranker(ABC):
    """Abstract interface for cross-encoder or neural reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        passages: list[RetrievedPassage],
        top_k: int,
    ) -> list[RetrievedPassage]:
        """Score and reorder candidate passages."""
        ...


class LLM(ABC):
    """Abstract interface for language model generation."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate complete text response."""
        ...

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Stream response tokens as a generator."""
        ...
