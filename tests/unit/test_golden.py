"""Unit tests for Golden QA dataset management, serialization, and partitioning."""

from pathlib import Path

from app.eval.golden import GoldenDatasetManager
from app.models.schemas import GoldenItem, GoldenQuestionType, GoldenSplit


def test_golden_manager_crud_and_partitioning(tmp_path: Path) -> None:
    """Verify item addition, retrieval, deletion, filtering, and train/holdout split."""
    manager = GoldenDatasetManager(storage_dir=tmp_path)

    # 1. Add items
    item1 = GoldenItem(
        id="item_1",
        question="What is the port?",
        reference_answer="8000",
        doc_id="doc1",
        page=1,
        type=GoldenQuestionType.FACTOID,
    )
    item2 = GoldenItem(
        id="item_2",
        question="How many pods?",
        reference_answer="12",
        doc_id="doc1",
        page=2,
        type=GoldenQuestionType.NUMERIC,
    )
    item3 = GoldenItem(
        id="item_3",
        question="What is the weather?",
        reference_answer="Don't know",
        doc_id="none",
        page=0,
        type=GoldenQuestionType.NO_ANSWER,
    )

    manager.add_item(item1)
    manager.add_item(item2)
    manager.add_item(item3)
    assert manager.count() == 3

    # 2. Get and filter
    assert manager.get_item("item_1") == item1
    assert manager.get_item("nonexistent") is None
    factoids = manager.list_items(q_type=GoldenQuestionType.FACTOID)
    assert len(factoids) == 1
    assert factoids[0].id == "item_1"

    # 3. Partitioning
    train_count, holdout_count = manager.partition_train_holdout(
        holdout_ratio=0.33, seed=42
    )
    assert train_count + holdout_count == 3
    assert holdout_count == 1
    assert train_count == 2

    # 4. Save and reload
    save_path = manager.save_to_file("test_golden.jsonl")
    assert save_path.exists()

    new_manager = GoldenDatasetManager(storage_dir=tmp_path)
    loaded_n = new_manager.load_from_file("test_golden.jsonl")
    assert loaded_n == 3
    assert new_manager.get_item("item_1") is not None
    assert new_manager.get_item("item_1").split in (
        GoldenSplit.TRAIN,
        GoldenSplit.HOLDOUT,
    )

    # 5. Delete
    deleted = manager.delete_item("item_1")
    assert deleted is True
    assert manager.count() == 2
    assert manager.get_item("item_1") is None
