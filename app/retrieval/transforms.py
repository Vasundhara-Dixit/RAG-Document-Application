"""Query transformation strategies: HyDE, Multi-Query expansion, and Step-Back prompting."""

from __future__ import annotations

import re
from typing import Any

from app.core.interfaces import LLM, Retriever
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.utils.logging import get_logger

logger = get_logger("query_transforms")


class QueryProcessor:
    """Orchestrates query transformations to improve retrieval recall and robustness."""

    def __init__(self, llm: LLM) -> None:
        """Initialize query processor with an LLM backend."""
        self.llm = llm

    def generate_hyde(self, query: str) -> str:
        """Generate a hypothetical document passage answering the query."""
        prompt = (
            "Write a concise, factual excerpt from a technical policy or system documentation "
            "that directly answers the following question. Do not include greetings, explanations, "
            "or conversational filler. Only write the excerpt.\n\n"
            f"Question: {query}\n\n"
            "Document Excerpt:"
        )
        try:
            passage = self.llm.generate(prompt=prompt).strip()
            # If the LLM generates a refusal or empty response, fall back to the query
            if not passage or "don't contain" in passage.lower():
                return query
            return passage
        except Exception as e:
            logger.warning("HyDE generation failed; falling back to original query", error=str(e))
            return query

    def generate_multi_query(self, query: str, num_variants: int = 3) -> list[str]:
        """Generate multiple distinct phrasing variations of the query."""
        prompt = (
            f"Generate {num_variants} alternative search queries that express the same intent as the question below. "
            "Use different technical terminology and phrasing to maximize search recall.\n"
            "Format: Output one query per line without bullet points, numbers, or quotation marks.\n\n"
            f"Question: {query}\n\n"
            "Alternative Queries:"
        )
        variants = [query]
        try:
            output = self.llm.generate(prompt=prompt).strip()
            for line in output.splitlines():
                cleaned = re.sub(r"^[\d\.\-\*\s]+", "", line).strip().strip('"\'')
                if cleaned and cleaned.lower() != query.lower() and len(cleaned) > 5:
                    variants.append(cleaned)
                    if len(variants) >= num_variants + 1:
                        break
        except Exception as e:
            logger.warning("Multi-query expansion failed", error=str(e))

        # Deduplicate while preserving order
        return list(dict.fromkeys(variants))

    def generate_step_back(self, query: str) -> str:
        """Generate a higher-level, foundational step-back question."""
        prompt = (
            "You are an expert at information retrieval. Given the specific question below, "
            "generate a more abstract, higher-level 'step-back' question that captures the broader "
            "system, policy, or concept behind it.\n"
            "Output ONLY the step-back question without commentary.\n\n"
            f"Specific Question: {query}\n\n"
            "Step-Back Question:"
        )
        try:
            step_back = self.llm.generate(prompt=prompt).strip()
            step_back = re.sub(r"^[\d\.\-\*\s]+", "", step_back).strip().strip('"\'')
            return step_back or query
        except Exception as e:
            logger.warning("Step-back generation failed", error=str(e))
            return query

    def retrieve_with_transform(
        self,
        retriever: Retriever,
        query: str,
        strategy: str = "none",
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        rrf_k: int = 60,
    ) -> list[RetrievedPassage]:
        """Execute retrieval augmented with the specified query transformation."""
        strat = strategy.lower().strip()

        if strat == "none" or not query.strip():
            return retriever.retrieve(query=query, top_k=top_k, filters=filters)

        if strat == "hyde":
            hypo_passage = self.generate_hyde(query)
            # Combine original query with hypothetical document to preserve intent and keyword matches
            augmented_query = f"{query} {hypo_passage}"
            return retriever.retrieve(query=augmented_query, top_k=top_k, filters=filters)

        if strat == "multi_query":
            variants = self.generate_multi_query(query=query, num_variants=3)
            chunk_map: dict[str, ChunkRecord] = {}
            rrf_scores: dict[str, float] = {}

            for q_variant in variants:
                passages = retriever.retrieve(query=q_variant, top_k=top_k * 2, filters=filters)
                for rank, p in enumerate(passages, start=1):
                    cid = p.chunk.chunk_id
                    chunk_map[cid] = p.chunk
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

            sorted_cids = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)
            return [
                RetrievedPassage(chunk=chunk_map[cid], score=round(rrf_scores[cid], 6))
                for cid in sorted_cids[:top_k]
            ]

        if strat == "step_back":
            step_back_q = self.generate_step_back(query)
            specific_passages = retriever.retrieve(query=query, top_k=top_k, filters=filters)
            step_back_passages = retriever.retrieve(query=step_back_q, top_k=top_k, filters=filters)

            chunk_map = {}
            rrf_scores = {}
            # Fuse specific query (weight 1.0) and step-back query (weight 0.7)
            for rank, p in enumerate(specific_passages, start=1):
                cid = p.chunk.chunk_id
                chunk_map[cid] = p.chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

            for rank, p in enumerate(step_back_passages, start=1):
                cid = p.chunk.chunk_id
                chunk_map[cid] = p.chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (0.7 / (rrf_k + rank))

            sorted_cids = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)
            return [
                RetrievedPassage(chunk=chunk_map[cid], score=round(rrf_scores[cid], 6))
                for cid in sorted_cids[:top_k]
            ]

        # Fallback if unknown strategy
        return retriever.retrieve(query=query, top_k=top_k, filters=filters)

