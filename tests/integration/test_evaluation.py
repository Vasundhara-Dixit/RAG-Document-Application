"""Integration tests for Phase 4 evaluation harness, benchmark runner, and reports."""

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.api.v1.routes import (
    PipelineServices,
    add_golden_item,
    list_eval_runs,
    list_golden_items,
    trigger_eval_run,
    upload_document,
)
from app.core.config import get_settings
from app.models.schemas import GoldenItem, GoldenQuestionType, GoldenSplit


@pytest.fixture
def eval_services(tmp_path: Path) -> PipelineServices:
    """Create isolated services for evaluation testing."""
    settings = get_settings().model_copy(deep=True)
    settings.ingestion.database_url = f"sqlite:///{tmp_path / 'eval.db'}"
    settings.ingestion.raw_data_dir = str(tmp_path / "raw")
    settings.indexing.chroma_persist_dir = str(tmp_path / "chroma")
    settings.indexing.faiss_index_path = str(tmp_path / "faiss.index")
    settings.eval.golden_set_dir = str(tmp_path / "golden")
    return PipelineServices(settings)


def test_eval_benchmark_flow(eval_services: PipelineServices, tmp_path: Path) -> None:
    """Verify end-to-end evaluation flow: ingestion, golden set, benchmark, and reporting."""
    # 1. Ingest test doc
    raw_content = b"""# Operations Manual
Page 1
Backups execute nightly at 02:00 UTC. AES-256 encryption is mandatory.
RTO target is 15 minutes.
"""
    mock_file = MagicMock()
    mock_file.filename = "ops_manual.txt"
    mock_file.content_type = "text/plain"
    mock_file.file = io.BytesIO(raw_content)

    doc_rec = upload_document(file=mock_file, services=eval_services)
    assert doc_rec.status.value == "ready"

    # 2. Add golden items (train + holdout)
    item_train = GoldenItem(
        id="eval_q1",
        question="When do nightly backups execute?",
        reference_answer="Backups execute nightly at 02:00 UTC.",
        doc_id=doc_rec.doc_id,
        page=1,
        type=GoldenQuestionType.FACTOID,
        split=GoldenSplit.TRAIN,
    )
    item_noans = GoldenItem(
        id="eval_q2",
        question="What is the lunch menu for the cafeteria?",
        reference_answer="The documents don't contain enough information to answer this.",
        doc_id="none",
        page=0,
        type=GoldenQuestionType.NO_ANSWER,
        split=GoldenSplit.TRAIN,
    )

    add_golden_item(item_train, services=eval_services)
    add_golden_item(item_noans, services=eval_services)

    items = list_golden_items(services=eval_services)
    assert len(items) == 2

    # 3. Trigger evaluation run
    eval_result = trigger_eval_run(split="train", top_k=3, services=eval_services)
    assert eval_result["item_count"] == 2
    metrics = eval_result["metrics"]
    assert "hit_at_1" in metrics
    assert "mrr" in metrics
    assert "faithfulness" in metrics
    assert eval_result["latency_p50_ms"] > 0

    # 4. Verify report generation
    reports_dir = Path("data/reports")
    csv_reports = list(reports_dir.glob(f"benchmark_{eval_result['run_id']}.csv"))
    md_reports = list(reports_dir.glob(f"benchmark_{eval_result['run_id']}.md"))
    assert len(csv_reports) == 1
    assert len(md_reports) == 1
    assert csv_reports[0].stat().st_size > 0
    assert md_reports[0].stat().st_size > 0

    # 5. Verify eval runs registry
    runs = list_eval_runs()
    assert len(runs) >= 1
    assert any(r.run_id == eval_result["run_id"] for r in runs)
