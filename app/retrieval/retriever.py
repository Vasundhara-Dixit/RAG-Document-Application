"""Retriever implementation supporting k-NN vector search and score filtering."""

from __future__ import annotations

from typing import Any

from app.core.config import RetrievalConfig, get_settings
from app.core.interfaces import Embedder, Retriever, VectorIndex
from app.models.schemas import RetrievedPassage
from app.utils.logging import get_logger

logger = get_logger("retriever")


class KNNRetriever(Retriever):
    """Nearest-neighbor retriever using dense embeddings and vector index."""

    def __init__(
        self,
        vector_index: VectorIndex,
        embedder: Embedder,
        config: RetrievalConfig | None = None,
    ) -> None:
        """Initialize retriever with index, embedder, and configuration."""
        self.vector_index = vector_index
        self.embedder = embedder
        self.config = config or get_settings().retrieval

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Retrieve passages matching natural language query."""
        if not query.strip():
            return []

        k = top_k if top_k is not None else self.config.default_k

        # 1. Embed query vector
        query_embedding = self.embedder.embed_query(query)

        # 2. Search nearest vectors in vector index
        passages = self.vector_index.search(
            query_embedding=query_embedding,
            top_k=k,
            filters=filters,
        )

        # 3. Apply score threshold
        threshold = self.config.score_threshold
        filtered_passages = [p for p in passages if p.score >= threshold]

        logger.info(
            "Retrieved passages",
            query=query[:60],
            requested_k=k,
            raw_count=len(passages),
            retained_count=len(filtered_passages),
        )
        return filtered_passages
