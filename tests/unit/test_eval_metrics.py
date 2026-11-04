"""Unit tests for retrieval evaluation metrics (Hit@K, MRR)."""

from app.eval.metrics import (
    QueryRetrievalResult,
    calculate_retrieval_metrics,
    compute_hit_rate,
    compute_mrr,
    is_hit_at_k,
    reciprocal_rank,
)


def test_hand_computed_retrieval_cases() -> None:
    """Verify hand-calculated Hit@K and MRR on a known 4-query dataset."""
    q1 = QueryRetrievalResult(
        query_id="q1",
        retrieved_chunk_ids=["c1", "c2", "c3", "c4", "c5"],
        relevant_chunk_ids=["c1"],  # Rank 1
    )
    q2 = QueryRetrievalResult(
        query_id="q2",
        retrieved_chunk_ids=["c1", "c2", "c3", "c4", "c5"],
        relevant_chunk_ids=["c3"],  # Rank 3
    )
    q3 = QueryRetrievalResult(
        query_id="q3",
        retrieved_chunk_ids=["c1", "c2", "c3", "c4", "c5"],
        relevant_chunk_ids=["c5"],  # Rank 5
    )
    q4 = QueryRetrievalResult(
        query_id="q4",
        retrieved_chunk_ids=["c1", "c2", "c3", "c4", "c5"],
        relevant_chunk_ids=["c99"],  # Not found
    )
    dataset = [q1, q2, q3, q4]

    # Hand-computed checks
    assert compute_hit_rate(dataset, k=1) == 0.25
    assert compute_hit_rate(dataset, k=3) == 0.50
    assert compute_hit_rate(dataset, k=5) == 0.75
    assert compute_hit_rate(dataset, k=10) == 0.75

    # MRR: (1.0 + 1/3 + 0.2 + 0.0) / 4 = 1.533333 / 4 = 0.3833
    assert compute_mrr(dataset) == 0.3833

    metrics = calculate_retrieval_metrics(dataset)
    assert metrics.hit_at_1 == 0.25
    assert metrics.hit_at_3 == 0.50
    assert metrics.hit_at_5 == 0.75
    assert metrics.hit_at_10 == 0.75
    assert metrics.mrr == 0.3833


def test_edge_cases_empty_and_zero_k() -> None:
    """Verify safe behavior on empty datasets and k=0."""
    assert compute_hit_rate([], k=5) == 0.0
    assert compute_mrr([]) == 0.0
    assert is_hit_at_k(["c1"], {"c1"}, k=0) is False
    assert is_hit_at_k([], {"c1"}, k=5) is False
    assert reciprocal_rank([], {"c1"}) == 0.0
    assert reciprocal_rank(["c1"], set()) == 0.0


def test_page_level_matching_with_tolerance() -> None:
    """Verify document page-level matching with tolerance window."""
    q_exact = QueryRetrievalResult(
        query_id="qp1",
        retrieved_pages=[("docA", 1), ("docA", 2), ("docB", 1)],
        relevant_pages=[("docA", 2)],
    )
    q_window = QueryRetrievalResult(
        query_id="qp2",
        retrieved_pages=[("docA", 5), ("docB", 1)],
        relevant_pages=[("docA", 6)],  # diff = 1
    )
    dataset = [q_exact, q_window]

    # Without tolerance (page_tolerance=0):
    # qp1 hits at rank 2. qp2 misses.
    hit1_strict = compute_hit_rate(dataset, k=1, use_page_match=True, page_tolerance=0)
    hit2_strict = compute_hit_rate(dataset, k=2, use_page_match=True, page_tolerance=0)
    assert hit1_strict == 0.0
    assert hit2_strict == 0.5

    # With tolerance=1:
    # Both qp1 (page 1 is within 1 of page 2) and qp2 (page 5 is within 1 of page 6) hit at rank 1.
    hit1_tol = compute_hit_rate(dataset, k=1, use_page_match=True, page_tolerance=1)
    assert hit1_tol == 1.0
