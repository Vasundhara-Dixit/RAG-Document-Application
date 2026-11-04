"""Hybrid retrieval combining dense vector search and sparse BM25 with Reciprocal Rank Fusion."""

from __future__ import annotations

from typing import Any

from app.core.interfaces import Retriever
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.retrieval.bm25 import BM25Index
from app.utils.logging import get_logger

logger = get_logger("hybrid_retriever")


class HybridRetriever(Retriever):
    """Fuses dense vector results and sparse BM25 results using Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        dense_retriever: Retriever,
        bm25_index: BM25Index,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0,
        candidate_multiplier: int = 4,
    ) -> None:
        """Initialize hybrid retriever.

        Args:
            dense_retriever: Underlying vector retriever (e.g. KNNRetriever).
            bm25_index: In-memory Okapi BM25 index.
            rrf_k: Smoothing constant for RRF (default: 60 per Cormack et al.).
            dense_weight: Relative weight multiplier for dense ranks.
            bm25_weight: Relative weight multiplier for BM25 ranks.
            candidate_multiplier: Factor to scale candidate pool before fusion.
        """
        self.dense_retriever = dense_retriever
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.candidate_multiplier = candidate_multiplier

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Retrieve passages combining dense semantic search and BM25 keyword matching."""
        if not query.strip():
            return []

        k = top_k if top_k is not None else 5
        candidate_k = max(k * self.candidate_multiplier, 50)

        # 1. Fetch dense candidates
        dense_passages = self.dense_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            filters=filters,
        )

        # 2. Fetch BM25 candidates
        bm25_hits = self.bm25_index.search(
            query=query,
            top_k=candidate_k,
            filters=filters,
        )

        # Map to track unique chunks and accumulate RRF scores
        chunk_map: dict[str, ChunkRecord] = {}
        rrf_scores: dict[str, float] = {}

        # 3. Score dense rank positions (1-indexed)
        for rank, passage in enumerate(dense_passages, start=1):
            cid = passage.chunk.chunk_id
            chunk_map[cid] = passage.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (
                self.dense_weight / (self.rrf_k + rank)
            )

        # 4. Score BM25 rank positions (1-indexed)
        for rank, (chunk, _bm25_score) in enumerate(bm25_hits, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (
                self.bm25_weight / (self.rrf_k + rank)
            )

        # 5. Sort candidates by combined RRF score
        sorted_cids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True,
        )

        # 6. Construct top-k RetrievedPassage results
        results = [
            RetrievedPassage(
                chunk=chunk_map[cid],
                score=round(rrf_scores[cid], 6),
            )
            for cid in sorted_cids[:k]
        ]

        logger.info(
            "Hybrid retrieval completed",
            query=query[:60],
            dense_count=len(dense_passages),
            bm25_count=len(bm25_hits),
            fused_candidates=len(rrf_scores),
            returned=len(results),
        )
        return results

