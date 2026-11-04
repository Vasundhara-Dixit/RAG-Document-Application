"""CLI benchmark execution and grid sweep script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.api.v1.routes import get_services
from app.eval.golden import GoldenDatasetManager
from app.eval.runner import BenchmarkRunner
from app.models.schemas import GoldenSplit


def ensure_corpus_indexed() -> None:
    """Ensure raw corpus documents in data/raw are ingested into the pipeline."""
    services = get_services()
    if services.vector_store.count() > 0:
        return

    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        return

    for doc_file in raw_dir.glob("*.*"):
        if doc_file.suffix.lower() not in [".txt", ".md", ".pdf", ".docx"]:
            continue
        try:
            raw_bytes = doc_file.read_bytes()
            mime = "text/plain" if doc_file.suffix == ".txt" else "text/markdown"
            rec, is_new = services.registry.register_document(
                filename=doc_file.name,
                file_bytes=raw_bytes,
                mime=mime,
            )
            parsed = services.parser.parse(
                file_bytes=raw_bytes,
                filename=doc_file.name,
                mime=mime,
                checksum=rec.checksum,
            )
            cleaned = services.cleaner.clean_document(parsed)
            chunks = services.chunker.chunk(
                doc=cleaned,
                embedding_model=services.embedder.model_name,
                config_hash=services.settings.get_config_hash(),
            )
            if chunks:
                embeddings = services.embedder.embed_texts([c.text for c in chunks])
                services.vector_store.add(chunks, embeddings)
                services.bm25_index.index_chunks(chunks)
            services.registry.update_status(
                doc_id=rec.doc_id,
                status="ready",
                pages=cleaned.total_pages,
            )
        except Exception as e:
            print(f"Skipping {doc_file.name}: {e}")


def main() -> None:
    """CLI entrypoint for running evaluation benchmarks."""
    parser = argparse.ArgumentParser(description="Execute RAG evaluation benchmark.")
    parser.add_argument(
        "--split",
        choices=["train", "holdout", "all"],
        default="train",
        help="Golden dataset partition to evaluate (default: train)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-K passages to retrieve (default: 5)",
    )
    parser.add_argument(
        "--golden-dir",
        default="data/golden",
        help="Directory containing golden dataset",
    )
    parser.add_argument(
        "--report-dir",
        default="data/reports",
        help="Directory to save benchmark reports",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Enable BM25 + dense hybrid retrieval with RRF",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Enable cross-encoder reranking (top-50 -> top-5)",
    )
    parser.add_argument(
        "--transform",
        choices=["none", "hyde", "multi_query", "step_back"],
        default="none",
        help="Query transformation strategy (default: none)",
    )
    args = parser.parse_args()

    # 1. Ingest corpus if index is empty
    ensure_corpus_indexed()

    # 2. Load dataset
    manager = GoldenDatasetManager(storage_dir=args.golden_dir)
    loaded = manager.load_from_file("golden_v1.jsonl")
    if loaded == 0:
        print("Golden dataset not found. Running build_golden...")
        from scripts.build_golden import create_golden_items

        items = create_golden_items()
        for it in items:
            manager.add_item(it)
        manager.partition_train_holdout()
        manager.save_to_file("golden_v1.jsonl")

    # 3. Setup and configure active retrieval strategy
    services = get_services()
    if args.hybrid:
        services.settings.retrieval.hybrid_enabled = True
        services.retriever.config.hybrid_enabled = True
    if args.rerank:
        services.settings.retrieval.reranker_enabled = True
        services.retriever.config.reranker_enabled = True
    if args.transform != "none":
        services.settings.retrieval.query_transform_strategy = args.transform
        services.retriever.config.query_transform_strategy = args.transform

    runner = BenchmarkRunner(services=services, golden_manager=manager)

    split_target = GoldenSplit.TRAIN if args.split == "train" else GoldenSplit.HOLDOUT
    summary = runner.run_benchmark(split=split_target, top_k=args.top_k)

    # 4. Export reports and log record
    csv_path, md_path = runner.export_reports(summary, output_dir=args.report_dir)
    runner.save_run_record(summary)

    # 5. Print summary report
    print("\n" + md_path.read_text(encoding="utf-8") + "\n")
    print(f"Reports exported:\n  - CSV: {csv_path}\n  - MD:  {md_path}\n")


if __name__ == "__main__":
    main()
