"""Unit tests for AnswerEvaluator semantic similarity and LLM-as-judge scoring."""

from app.core.config import EmbeddingConfig
from app.eval.evaluator import AnswerEvaluator
from app.indexing.embedder import MockEmbedder
from app.models.schemas import ChunkRecord, RetrievedPassage


def test_semantic_similarity_and_abstention() -> None:
    """Verify semantic similarity and abstention handling."""
    embedder = MockEmbedder(EmbeddingConfig())
    evaluator = AnswerEvaluator(embedder=embedder)

    # 1. Identical text
    sim_identical = evaluator.compute_semantic_similarity(
        "Acme revenue was $42M", "Acme revenue was $42M"
    )
    assert sim_identical >= 0.99

    # 2. Both abstained
    sim_both_abstain = evaluator.compute_semantic_similarity(
        "The documents don't contain enough information to answer this.",
        "The documents do not contain enough information.",
    )
    assert sim_both_abstain == 1.0

    # 3. One abstained, one didn't
    sim_one_abstain = evaluator.compute_semantic_similarity(
        "The documents don't contain enough information to answer this.",
        "Revenue was $42 million in Q3 2026.",
    )
    assert sim_one_abstain == 0.0


def test_judge_json_parsing() -> None:
    """Verify JSON parsing of judge scores and normalization from 1-5 to 0.0-1.0."""
    embedder = MockEmbedder(EmbeddingConfig())
    evaluator = AnswerEvaluator(embedder=embedder)

    raw_json = """
    ```json
    {
      "faithfulness": 5,
      "correctness": 4,
      "completeness": 3,
      "reasoning": "Well grounded, minor missing detail."
    }
    ```
    """
    f, c, comp, reason = evaluator._parse_judge_json(raw_json)
    # (5-1)/4 = 1.0
    assert f == 1.0
    # (4-1)/4 = 0.75
    assert c == 0.75
    # (3-1)/4 = 0.50
    assert comp == 0.50
    assert "Well grounded" in reason


def test_offline_judge_scoring() -> None:
    """Verify deterministic offline judge assessment logic."""
    embedder = MockEmbedder(EmbeddingConfig())
    evaluator = AnswerEvaluator(embedder=embedder)

    chunk = ChunkRecord(
        chunk_id="c1",
        doc_id="server_ops_manual.txt",
        idx=0,
        text="Backups execute nightly at 02:00 UTC with 30 daily snapshots.",
        token_count=10,
        page_start=2,
        page_end=2,
        char_start=0,
        char_end=60,
        embedding_model="mock",
        config_hash="abc",
    )
    passages = [RetrievedPassage(chunk=chunk, score=0.92, rank=1)]

    # Grounded answer matching reference
    res = evaluator.evaluate_answer(
        item_id="q1",
        question="When do backups execute?",
        contexts=passages,
        generated_answer="Backups execute nightly at 02:00 UTC with 30 daily snapshots.",
        reference_answer="Backups execute nightly at 02:00 UTC.",
    )
    assert res.faithfulness >= 0.8
    assert res.correctness >= 0.8
    assert res.completeness >= 0.8

    # Out of domain query correctly abstained
    abs_res = evaluator.evaluate_answer(
        item_id="q2",
        question="What is the lunch menu?",
        contexts=[],
        generated_answer="The documents don't contain enough information to answer this.",
        reference_answer="The documents don't contain enough information to answer this.",
    )
    assert abs_res.faithfulness == 1.0
    assert abs_res.correctness == 1.0
    assert abs_res.completeness == 1.0
