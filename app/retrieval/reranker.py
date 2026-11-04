"""Cross-encoder reranking implementations for candidate re-scoring."""

from __future__ import annotations

import math
import re
from typing import Any

from app.core.interfaces import LLM, Reranker
from app.models.schemas import RetrievedPassage
from app.retrieval.bm25 import tokenize_bm25
from app.utils.logging import get_logger

logger = get_logger("reranker")


class FastCrossEncoderReranker(Reranker):
    """Deterministic high-speed cross-encoder computing query-passage token interactions.

    Scores candidate passages using:
    1. Query term coverage (recall of query terms in the passage).
    2. Exact phrase matching bonus (contiguous n-gram alignment).
    3. Positional span compactness (proximity of matching terms).
    4. Base bi-encoder retrieval score fusion.
    """

    def __init__(
        self,
        alpha_coverage: float = 0.40,
        alpha_base_score: float = 0.30,
        alpha_phrase: float = 0.20,
        alpha_proximity: float = 0.10,
    ) -> None:
        """Initialize reranker with interaction weights."""
        self.alpha_coverage = alpha_coverage
        self.alpha_base_score = alpha_base_score
        self.alpha_phrase = alpha_phrase
        self.alpha_proximity = alpha_proximity

    def _compute_span_proximity(
        self, query_terms: list[str], passage_tokens: list[str]
    ) -> float:
        """Calculate span compactness score based on minimum token window containing matches."""
        positions: list[int] = []
        for i, tok in enumerate(passage_tokens):
            if tok in query_terms:
                positions.append(i)

        if len(positions) < 2:
            return 1.0 if len(positions) == 1 else 0.0

        min_span = float("inf")
        # Find shortest window covering at least min(3, len(query_terms)) distinct terms
        left = 0
        window_counts: dict[str, int] = {}

        for right in range(len(positions)):
            pos_right = positions[right]
            term = passage_tokens[pos_right]
            window_counts[term] = window_counts.get(term, 0) + 1

            while len(window_counts) >= min(len(query_terms), 3):
                span_len = positions[right] - positions[left] + 1
                if span_len < min_span:
                    min_span = span_len
                left_term = passage_tokens[positions[left]]
                window_counts[left_term] -= 1
                if window_counts[left_term] == 0:
                    del window_counts[left_term]
                left += 1

        if min_span == float("inf"):
            # Fallback to distance between first and last match
            span_len = positions[-1] - positions[0] + 1
            min_span = span_len

        # Score decaying with window length
        return 1.0 / (1.0 + math.log(max(1, min_span)))

    def score_pair(self, query: str, passage: RetrievedPassage) -> float:
        """Compute cross-encoder interaction score for a (query, passage) pair."""
        q_tokens = tokenize_bm25(query)
        if not q_tokens:
            return passage.score

        p_tokens = tokenize_bm25(passage.chunk.text)
        if not p_tokens:
            return 0.0

        q_terms_set = set(q_tokens)
        p_terms_set = set(p_tokens)

        # 1. Term coverage ratio
        matched_q_terms = q_terms_set.intersection(p_terms_set)
        coverage_score = len(matched_q_terms) / len(q_terms_set)

        # 2. Exact phrase bonus
        clean_query = " ".join(q_tokens)
        clean_passage = " ".join(p_tokens)
        phrase_score = 1.0 if clean_query in clean_passage else 0.0
        if not phrase_score and len(q_tokens) >= 3:
            # Check 3-gram sub-phrases
            for i in range(len(q_tokens) - 2):
                tri = f"{q_tokens[i]} {q_tokens[i+1]} {q_tokens[i+2]}"
                if tri in clean_passage:
                    phrase_score = max(phrase_score, 0.5)

        # 3. Proximity score
        proximity_score = self._compute_span_proximity(q_tokens, p_tokens)

        # 4. Normalized base score (clip to [0, 1])
        base_norm = max(0.0, min(1.0, (passage.score + 1.0) / 2.0))

        # Composite score
        rerank_score = (
            self.alpha_coverage * coverage_score
            + self.alpha_phrase * phrase_score
            + self.alpha_proximity * proximity_score
            + self.alpha_base_score * base_norm
        )
        return round(rerank_score, 6)

    def rerank(
        self,
        query: str,
        passages: list[RetrievedPassage],
        top_k: int,
    ) -> list[RetrievedPassage]:
        """Score and reorder candidate passages."""
        if not passages or not query.strip():
            return []

        scored_passages: list[RetrievedPassage] = []
        for p in passages:
            new_score = self.score_pair(query, p)
            scored_passages.append(
                RetrievedPassage(
                    chunk=p.chunk,
                    score=new_score,
                )
            )

        # Sort descending by recomputed cross-encoder score
        scored_passages.sort(key=lambda p: p.score, reverse=True)

        logger.info(
            "Reranked candidate passages",
            query=query[:60],
            candidates=len(passages),
            retained=min(top_k, len(scored_passages)),
        )
        return scored_passages[:top_k]


class LLMCrossEncoderReranker(Reranker):
    """Cross-encoder reranker utilizing an LLM to score passage relevance."""

    def __init__(self, llm: LLM, prompt_template: str | None = None) -> None:
        """Initialize with LLM client."""
        self.llm = llm
        self.prompt_template = prompt_template or (
            "Rate the relevance of the following document passage to the question on a scale of 0 to 10.\n"
            "Respond ONLY with a single numeric integer between 0 and 10.\n\n"
            "Question: {question}\n\n"
            "Passage:\n{passage}\n\n"
            "Score:"
        )

    def rerank(
        self,
        query: str,
        passages: list[RetrievedPassage],
        top_k: int,
    ) -> list[RetrievedPassage]:
        """Score and reorder candidate passages using LLM relevance judgments."""
        if not passages or not query.strip():
            return []

        scored: list[tuple[RetrievedPassage, float]] = []
        for p in passages:
            prompt = self.prompt_template.format(
                question=query,
                passage=p.chunk.text[:800],
            )
            try:
                response = self.llm.generate(prompt=prompt)
                match = re.search(r"\b([0-9]|10)\b", response)
                score_val = float(match.group(1)) / 10.0 if match else p.score
            except Exception as e:
                logger.warning("LLM reranking failed for passage; falling back to base score", error=str(e))
                score_val = p.score

            scored.append((RetrievedPassage(chunk=p.chunk, score=round(score_val, 4)), score_val))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:top_k]]


def get_reranker(
    reranker_type: str = "fast",
    llm: LLM | None = None,
    **kwargs: Any,
) -> Reranker:
    """Factory creating appropriate Reranker instance."""
    if reranker_type.lower() == "llm" and llm is not None:
        return LLMCrossEncoderReranker(llm=llm, **kwargs)
    return FastCrossEncoderReranker(**kwargs)
