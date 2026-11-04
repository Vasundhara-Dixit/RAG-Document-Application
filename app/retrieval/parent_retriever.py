"""Small-to-big hierarchical parent document retriever."""

from __future__ import annotations

from typing import Any

from app.core.interfaces import Retriever
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.utils.logging import get_logger

logger = get_logger("parent_retriever")


class ParentDocumentRetriever(Retriever):
    """Small-to-big retriever that searches child chunks and returns parent contexts."""

    def __init__(
        self,
        child_retriever: Retriever,
        parent_store: dict[str, ChunkRecord] | None = None,
    ) -> None:
        """Initialize with child retriever and parent chunk storage."""
        self.child_retriever = child_retriever
        self.parent_store: dict[str, ChunkRecord] = parent_store or {}

    def register_parents(self, parent_chunks: list[ChunkRecord]) -> None:
        """Store parent chunks in registry."""
        for p in parent_chunks:
            self.parent_store[p.chunk_id] = p
        logger.info("Registered parent chunks", count=len(parent_chunks), total=len(self.parent_store))

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Retrieve child passages and resolve to expanded parent chunks."""
        k = top_k if top_k is not None else 5
        # Fetch 2x candidates to allow for deduplication when multiple children share a parent
        child_passages = self.child_retriever.retrieve(
            query=query,
            top_k=k * 2,
            filters=filters,
        )

        seen_parents: set[str] = set()
        parent_passages: list[RetrievedPassage] = []

        for p in child_passages:
            pid = p.chunk.parent_id
            if pid and pid in self.parent_store:
                if pid not in seen_parents:
                    seen_parents.add(pid)
                    parent_passages.append(
                        RetrievedPassage(
                            chunk=self.parent_store[pid],
                            score=p.score,
                        )
                    )
            else:
                # If chunk has no parent or parent not found, preserve the chunk itself
                if p.chunk.chunk_id not in seen_parents:
                    seen_parents.add(p.chunk.chunk_id)
                    parent_passages.append(p)

            if len(parent_passages) >= k:
                break

        logger.info(
            "Parent document retrieval resolved",
            query=query[:60],
            child_matches=len(child_passages),
            parent_contexts=len(parent_passages),
        )
        return parent_passages

