"""Unified advanced retrieval orchestrator coordinating hybrid search, reranking, and transformations."""

from __future__ import annotations

from typing import Any

from app.core.config import RetrievalConfig, get_settings
from app.core.interfaces import LLM, Reranker, Retriever
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.parent_retriever import ParentDocumentRetriever
from app.retrieval.reranker import get_reranker
from app.retrieval.transforms import QueryProcessor
from app.utils.logging import get_logger

logger = get_logger("advanced_retriever")


class AdvancedRetriever(Retriever):
    """Configurable pipeline orchestrator supporting Dense, BM25 Hybrid, Reranking, Transformations, and Hierarchy."""

    def __init__(
        self,
        dense_retriever: Retriever,
        bm25_index: BM25Index,
        llm: LLM,
        config: RetrievalConfig | None = None,
        parent_store: dict[str, ChunkRecord] | None = None,
    ) -> None:
        """Initialize advanced retriever components."""
        self.dense_retriever = dense_retriever
        self.bm25_index = bm25_index
        self.config = config or get_settings().retrieval
        self.parent_store: dict[str, ChunkRecord] = parent_store or {}

        # 1. Hybrid retriever
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=self.dense_retriever,
            bm25_index=self.bm25_index,
            rrf_k=self.config.rrf_k,
            dense_weight=self.config.dense_weight,
            bm25_weight=self.config.bm25_weight,
        )

        # 2. Parent document retriever
        active_child = (
            self.hybrid_retriever
            if self.config.hybrid_enabled
            else self.dense_retriever
        )
        self.parent_retriever = ParentDocumentRetriever(
            child_retriever=active_child,
            parent_store=self.parent_store,
        )

        # 3. Reranker
        self.reranker: Reranker = get_reranker(
            reranker_type=self.config.reranker_type,
            llm=llm,
        )

        # 4. Query processor
        self.query_processor = QueryProcessor(llm=llm)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
        hybrid_enabled: bool | None = None,
        reranker_enabled: bool | None = None,
        query_transform_strategy: str | None = None,
    ) -> list[RetrievedPassage]:
        """Orchestrate retrieval through active enhancement pipeline."""
        if not query.strip():
            return []

        k = top_k if top_k is not None else self.config.default_k

        # Effective toggles
        use_hybrid = (
            hybrid_enabled
            if hybrid_enabled is not None
            else self.config.hybrid_enabled
        )
        use_reranker = (
            reranker_enabled
            if reranker_enabled is not None
            else self.config.reranker_enabled
        )
        active_transform = (
            query_transform_strategy
            if query_transform_strategy is not None
            else self.config.query_transform_strategy
        )

        # Determine base candidate retriever
        if self.config.parent_retrieval_enabled:
            base: Retriever = self.parent_retriever
        elif use_hybrid:
            base = self.hybrid_retriever
        else:
            base = self.dense_retriever

        candidate_k = (
            max(self.config.reranker_candidates, k)
            if use_reranker
            else k
        )

        # 1. Query transformations
        strat = active_transform.lower().strip()
        if strat != "none":
            passages = self.query_processor.retrieve_with_transform(
                retriever=base,
                query=query,
                strategy=strat,
                top_k=candidate_k,
                filters=filters,
                rrf_k=self.config.rrf_k,
            )
        else:
            passages = base.retrieve(
                query=query,
                top_k=candidate_k,
                filters=filters,
            )

        # 2. Cross-encoder reranking
        if use_reranker and passages:
            passages = self.reranker.rerank(
                query=query,
                passages=passages,
                top_k=k,
            )

        # 3. Score threshold filtering (only if threshold is positive)
        if self.config.score_threshold > 0.0:
            passages = [p for p in passages if p.score >= self.config.score_threshold]

        return passages[:k]

