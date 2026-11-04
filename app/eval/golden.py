"""Golden dataset management, serialization, and train/holdout partitioning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.schemas import GoldenItem, GoldenQuestionType, GoldenSplit
from app.utils.logging import get_logger

logger = get_logger("golden_dataset")


class GoldenDatasetManager:
    """Manages loading, persistence, and querying of Golden QA benchmark items."""

    def __init__(self, storage_dir: str | Path = "data/golden") -> None:
        """Initialize dataset manager with target storage directory."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._items: dict[str, GoldenItem] = {}

    def add_item(self, item: GoldenItem) -> None:
        """Add or update a golden QA benchmark item."""
        self._items[item.id] = item

    def get_item(self, item_id: str) -> GoldenItem | None:
        """Retrieve a golden QA item by unique identifier."""
        return self._items.get(item_id)

    def delete_item(self, item_id: str) -> bool:
        """Delete an item by identifier; returns True if item was removed."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def list_items(
        self,
        split: GoldenSplit | str | None = None,
        q_type: GoldenQuestionType | str | None = None,
        doc_id: str | None = None,
        version: str | None = None,
    ) -> list[GoldenItem]:
        """Filter golden QA items by partition split, taxonomy type, doc_id, or version."""
        split_val = split.value if isinstance(split, GoldenSplit) else split
        type_val = q_type.value if isinstance(q_type, GoldenQuestionType) else q_type

        filtered: list[GoldenItem] = []
        for item in self._items.values():
            if split_val and item.split.value != split_val:
                continue
            if type_val and item.type.value != type_val:
                continue
            if doc_id and item.doc_id != doc_id:
                continue
            if version and item.version != version:
                continue
            filtered.append(item)
        return filtered

    def count(self) -> int:
        """Return total count of loaded golden items."""
        return len(self._items)

    def save_to_file(self, filename: str = "golden_v1.jsonl") -> Path:
        """Persist in-memory items to a JSON Lines file."""
        out_path = self.storage_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            for item in self._items.values():
                f.write(item.model_dump_json() + "\n")
        logger.info("Saved golden dataset", path=str(out_path), count=len(self._items))
        return out_path

    def load_from_file(self, filename: str = "golden_v1.jsonl") -> int:
        """Load items from a JSON Lines file into memory."""
        file_path = self.storage_dir / filename
        if not file_path.exists():
            logger.warn("Golden dataset file does not exist", path=str(file_path))
            return 0

        loaded = 0
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                data: dict[str, Any] = json.loads(line_str)
                item = GoldenItem(**data)
                self._items[item.id] = item
                loaded += 1

        logger.info("Loaded golden dataset", path=str(file_path), count=loaded)
        return loaded

    def partition_train_holdout(
        self,
        holdout_ratio: float = 0.30,
        seed: int = 42,
    ) -> tuple[int, int]:
        """Enforce deterministic 70/30 train/holdout partition per ADR-004."""
        import random

        rng = random.Random(seed)
        all_ids = sorted(self._items.keys())
        rng.shuffle(all_ids)

        holdout_count = (
            max(1, round(len(all_ids) * holdout_ratio))
            if (holdout_ratio > 0 and len(all_ids) > 1)
            else int(len(all_ids) * holdout_ratio)
        )
        holdout_ids = set(all_ids[:holdout_count])

        train_total = 0
        holdout_total = 0

        for item_id, item in self._items.items():
            if item_id in holdout_ids:
                item.split = GoldenSplit.HOLDOUT
                holdout_total += 1
            else:
                item.split = GoldenSplit.TRAIN
                train_total += 1

        logger.info(
            "Partitioned golden set",
            train_count=train_total,
            holdout_count=holdout_total,
            ratio=holdout_ratio,
        )
        return train_total, holdout_total
