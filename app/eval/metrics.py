"""Retrieval evaluation metrics: Hit Rate@K, MRR, and rank-aware statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.schemas import EvalMetrics


@dataclass
class QueryRetrievalResult:
    """Evaluation container for a single query's retrieved items vs ground truth."""

    query_id: str
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[str] = field(default_factory=list)
    retrieved_pages: list[tuple[Any, ...]] = field(
        default_factory=list
    )  # (doc_id, page) or (doc_id, p_start, p_end)
    relevant_pages: list[tuple[str, int]] = field(
        default_factory=list
    )  # (doc_id, page)


def is_hit_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int,
) -> bool:
    """Check if any relevant item appears in the top-k retrieved list."""
    if not relevant or k <= 0:
        return False
    top_k = retrieved[:k]
    return any(item in relevant for item in top_k)


def reciprocal_rank(
    retrieved: list[str],
    relevant: set[str],
) -> float:
    """Compute Reciprocal Rank: 1 / rank of first relevant item (1-based), or 0.0."""
    if not relevant:
        return 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def _page_matches(
    r_tuple: tuple[Any, ...], gt_doc: str, gt_page: int, page_tolerance: int
) -> bool:
    """Helper to check if a retrieved page/page-range matches ground truth."""
    if len(r_tuple) >= 3:
        r_doc, r_start, r_end = r_tuple[0], int(r_tuple[1]), int(r_tuple[2])
        return bool(
            r_doc == gt_doc
            and (r_start - page_tolerance <= gt_page <= r_end + page_tolerance)
        )
    elif len(r_tuple) == 2:
        r_doc, r_page = r_tuple[0], int(r_tuple[1])
        return bool(r_doc == gt_doc and abs(r_page - gt_page) <= page_tolerance)
    return False


def compute_hit_rate(
    results: list[QueryRetrievalResult],
    k: int,
    use_page_match: bool = False,
    page_tolerance: int = 0,
) -> float:
    """Compute Hit Rate@K across all evaluated answerable queries."""
    if not results:
        return 0.0

    answerable = [
        res
        for res in results
        if (res.relevant_pages if use_page_match else res.relevant_chunk_ids)
    ]
    if not answerable:
        return 0.0

    hits = 0
    for res in answerable:
        if use_page_match:
            rel_pages = res.relevant_pages
            hit = False
            for r_tuple in res.retrieved_pages[:k]:
                for gt_doc, gt_page in rel_pages:
                    if _page_matches(r_tuple, gt_doc, gt_page, page_tolerance):
                        hit = True
                        break
                if hit:
                    break
            if hit:
                hits += 1
        else:
            rel_set = set(res.relevant_chunk_ids)
            if is_hit_at_k(res.retrieved_chunk_ids, rel_set, k):
                hits += 1

    return round(hits / len(answerable), 4)


def compute_mrr(
    results: list[QueryRetrievalResult],
    use_page_match: bool = False,
    page_tolerance: int = 0,
) -> float:
    """Compute Mean Reciprocal Rank (MRR) across all evaluated answerable queries."""
    if not results:
        return 0.0

    answerable = [
        res
        for res in results
        if (res.relevant_pages if use_page_match else res.relevant_chunk_ids)
    ]
    if not answerable:
        return 0.0

    rr_sum = 0.0
    for res in answerable:
        if use_page_match:
            rel_pages = res.relevant_pages
            found_rr = 0.0
            for rank, r_tuple in enumerate(res.retrieved_pages, start=1):
                match = any(
                    _page_matches(r_tuple, gt_doc, gt_page, page_tolerance)
                    for gt_doc, gt_page in rel_pages
                )
                if match:
                    found_rr = 1.0 / rank
                    break
            rr_sum += found_rr
        else:
            rel_set = set(res.relevant_chunk_ids)
            rr_sum += reciprocal_rank(res.retrieved_chunk_ids, rel_set)

    return round(rr_sum / len(answerable), 4)


def calculate_retrieval_metrics(
    results: list[QueryRetrievalResult],
    use_page_match: bool = False,
    page_tolerance: int = 0,
) -> EvalMetrics:
    """Calculate standard retrieval metrics (Hit@1, 3, 5, 10 and MRR)."""
    return EvalMetrics(
        hit_at_1=compute_hit_rate(
            results, k=1, use_page_match=use_page_match, page_tolerance=page_tolerance
        ),
        hit_at_3=compute_hit_rate(
            results, k=3, use_page_match=use_page_match, page_tolerance=page_tolerance
        ),
        hit_at_5=compute_hit_rate(
            results, k=5, use_page_match=use_page_match, page_tolerance=page_tolerance
        ),
        hit_at_10=compute_hit_rate(
            results, k=10, use_page_match=use_page_match, page_tolerance=page_tolerance
        ),
        mrr=compute_mrr(
            results, use_page_match=use_page_match, page_tolerance=page_tolerance
        ),
    )
