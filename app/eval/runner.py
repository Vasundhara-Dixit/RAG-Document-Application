"""Experiment runner orchestrating retrieval and generation benchmark sweeps."""

from __future__ import annotations

import csv
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.api.v1.routes import PipelineServices
from app.eval.evaluator import AnswerEvaluationResult, AnswerEvaluator
from app.eval.golden import GoldenDatasetManager
from app.eval.metrics import QueryRetrievalResult, calculate_retrieval_metrics
from app.models.schemas import EvalMetrics, EvalRunRecord, GoldenItem, GoldenSplit
from app.utils.logging import get_logger

logger = get_logger("eval_runner")


@dataclass
class SingleItemRunResult:
    """Detailed trace and evaluation of a single golden QA item execution."""

    item: GoldenItem
    retrieval_result: QueryRetrievalResult
    answer_result: AnswerEvaluationResult
    retrieval_ms: float
    generation_ms: float
    total_ms: float
    abstained: bool


@dataclass
class BenchmarkSummary:
    """Aggregated quantitative results of a benchmark run."""

    run_id: str
    config_hash: str
    split: str
    item_count: int
    metrics: EvalMetrics
    mean_semantic_similarity: float
    latency_p50_ms: float
    latency_p95_ms: float
    item_results: list[SingleItemRunResult]


class BenchmarkRunner:
    """Executes evaluation benchmarks across dataset splits and parameter grids."""

    def __init__(
        self,
        services: PipelineServices,
        golden_manager: GoldenDatasetManager,
    ) -> None:
        """Initialize runner with active pipeline services and dataset manager."""
        self.services = services
        self.golden_manager = golden_manager
        self.evaluator = AnswerEvaluator(embedder=services.embedder)

    def run_benchmark(
        self,
        split: GoldenSplit | str = GoldenSplit.TRAIN,
        top_k: int = 5,
        run_id: str | None = None,
    ) -> BenchmarkSummary:
        """Execute benchmark over specified dataset split."""
        split_val = split.value if isinstance(split, GoldenSplit) else split
        items = self.golden_manager.list_items(split=split_val)
        if not items:
            # Fallback if split has no items: load from default golden file
            self.golden_manager.load_from_file("golden_v1.jsonl")
            items = self.golden_manager.list_items(split=split_val)

        active_run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        config_hash = self.services.settings.get_config_hash()

        logger.info(
            "Starting benchmark execution",
            run_id=active_run_id,
            split=split_val,
            item_count=len(items),
            top_k=top_k,
        )

        item_results: list[SingleItemRunResult] = []
        retrieval_cases: list[QueryRetrievalResult] = []
        total_latencies: list[float] = []

        faithfulness_scores: list[float] = []
        correctness_scores: list[float] = []
        completeness_scores: list[float] = []
        similarity_scores: list[float] = []

        doc_map = {
            d.doc_id: d.filename for d in self.services.registry.list_documents()
        }

        for item in items:
            t0 = time.perf_counter()

            # 1. Retrieval
            t_ret_start = time.perf_counter()
            passages = self.services.retriever.retrieve(
                query=item.question,
                top_k=top_k,
            )
            ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

            ret_chunk_ids = [p.chunk.chunk_id for p in passages]
            ret_pages = [
                (
                    doc_map.get(p.chunk.doc_id, p.chunk.doc_id),
                    p.chunk.page_start,
                    p.chunk.page_end,
                )
                for p in passages
            ]

            # Match against target doc_id and page (or filename match)
            if item.doc_id and item.doc_id.lower() != "none":
                rel_pages = [(item.doc_id, item.page)]
                rel_chunk_ids = item.chunk_ids
            else:
                rel_pages = []
                rel_chunk_ids = []

            ret_case = QueryRetrievalResult(
                query_id=item.id,
                retrieved_chunk_ids=ret_chunk_ids,
                relevant_chunk_ids=rel_chunk_ids,
                retrieved_pages=ret_pages,
                relevant_pages=rel_pages,
            )
            retrieval_cases.append(ret_case)

            # 2. Grounded Generation
            t_gen_start = time.perf_counter()
            system_prompt = self.services.prompt_builder.build_system_prompt()
            user_prompt = self.services.prompt_builder.build_user_prompt(
                question=item.question,
                passages=passages,
            )
            raw_answer = self.services.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
            tot_ms = (time.perf_counter() - t0) * 1000.0
            total_latencies.append(tot_ms)

            abstained = self.services.prompt_builder.is_abstained(raw_answer)

            # 3. Answer Evaluation
            ans_res = self.evaluator.evaluate_answer(
                item_id=item.id,
                question=item.question,
                contexts=passages,
                generated_answer=raw_answer,
                reference_answer=item.reference_answer,
            )

            faithfulness_scores.append(ans_res.faithfulness)
            correctness_scores.append(ans_res.correctness)
            completeness_scores.append(ans_res.completeness)
            similarity_scores.append(ans_res.semantic_similarity)

            item_results.append(
                SingleItemRunResult(
                    item=item,
                    retrieval_result=ret_case,
                    answer_result=ans_res,
                    retrieval_ms=round(ret_ms, 2),
                    generation_ms=round(gen_ms, 2),
                    total_ms=round(tot_ms, 2),
                    abstained=abstained,
                )
            )

        # 4. Aggregations
        ret_metrics = calculate_retrieval_metrics(
            retrieval_cases,
            use_page_match=True,
            page_tolerance=1,
        )

        n = len(items) if items else 1
        mean_faith = round(sum(faithfulness_scores) / n, 4)
        mean_corr = round(sum(correctness_scores) / n, 4)
        mean_comp = round(sum(completeness_scores) / n, 4)
        mean_sim = round(sum(similarity_scores) / n, 4)

        ret_metrics.faithfulness = mean_faith
        ret_metrics.correctness = mean_corr
        ret_metrics.completeness = mean_comp

        sorted_latencies = sorted(total_latencies)
        p50_idx = int(len(sorted_latencies) * 0.50)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p50 = round(sorted_latencies[p50_idx], 2) if sorted_latencies else 0.0
        p95 = (
            round(sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)], 2)
            if sorted_latencies
            else 0.0
        )

        return BenchmarkSummary(
            run_id=active_run_id,
            config_hash=config_hash,
            split=split_val,
            item_count=len(items),
            metrics=ret_metrics,
            mean_semantic_similarity=mean_sim,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
            item_results=item_results,
        )

    def export_reports(
        self,
        summary: BenchmarkSummary,
        output_dir: str | Path = "data/reports",
    ) -> tuple[Path, Path]:
        """Export benchmark summary as CSV and formatted Markdown report."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        csv_path = out_dir / f"benchmark_{summary.run_id}.csv"
        md_path = out_dir / f"benchmark_{summary.run_id}.md"

        # 1. Export CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "item_id",
                    "question_type",
                    "question",
                    "reference_answer",
                    "generated_answer",
                    "abstained",
                    "semantic_similarity",
                    "faithfulness",
                    "correctness",
                    "completeness",
                    "retrieval_ms",
                    "generation_ms",
                    "total_ms",
                ]
            )
            for r in summary.item_results:
                writer.writerow(
                    [
                        r.item.id,
                        r.item.type.value,
                        r.item.question,
                        r.item.reference_answer,
                        r.answer_result.generated_answer,
                        r.abstained,
                        r.answer_result.semantic_similarity,
                        r.answer_result.faithfulness,
                        r.answer_result.correctness,
                        r.answer_result.completeness,
                        r.retrieval_ms,
                        r.generation_ms,
                        r.total_ms,
                    ]
                )

        # 2. Export Markdown Report
        m = summary.metrics
        md_content = f"""# Benchmark Report: `{summary.run_id}`

- **Split:** `{summary.split}`
- **Items Evaluated:** {summary.item_count}
- **Config Hash:** `{summary.config_hash}`
- **p50 Latency:** {summary.latency_p50_ms} ms
- **p95 Latency:** {summary.latency_p95_ms} ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | {m.hit_at_1:.4f} | — | — |
| Hit Rate@3 | {m.hit_at_3:.4f} | — | — |
| Hit Rate@5 | {m.hit_at_5:.4f} | >= 0.8500 | {"PASS" if m.hit_at_5 >= 0.85 else "FLAG"} |
| Hit Rate@10 | {m.hit_at_10:.4f} | — | — |
| MRR | {m.mrr:.4f} | >= 0.6500 | {"PASS" if m.mrr >= 0.65 else "FLAG"} |
| Faithfulness | {m.faithfulness or 0.0:.4f} | >= 0.9000 | {"PASS" if (m.faithfulness or 0.0) >= 0.90 else "FLAG"} |
| Correctness | {m.correctness or 0.0:.4f} | — | — |
| Completeness | {m.completeness or 0.0:.4f} | — | — |
| Mean Semantic Sim | {summary.mean_semantic_similarity:.4f} | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
"""
        for r in summary.item_results[:10]:
            q_short = (
                (r.item.question[:45] + "...")
                if len(r.item.question) > 45
                else r.item.question
            )
            md_content += (
                f"| `{r.item.id}` | {r.item.type.value} | {q_short} | "
                f"{r.answer_result.semantic_similarity:.2f} | {r.answer_result.faithfulness:.2f} | "
                f"{r.answer_result.correctness:.2f} | {r.total_ms} |\n"
            )

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info("Exported benchmark reports", csv=str(csv_path), md=str(md_path))
        return csv_path, md_path

    def save_run_record(
        self,
        summary: BenchmarkSummary,
        storage_file: str | Path = "data/eval_runs.jsonl",
    ) -> EvalRunRecord:
        """Persist structured benchmark run record to JSONL registry."""
        path = Path(storage_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        record = EvalRunRecord(
            run_id=summary.run_id,
            config_hash=summary.config_hash,
            dataset_version="v1.0",
            metrics=summary.metrics,
            latency_p50_ms=summary.latency_p50_ms,
            latency_p95_ms=summary.latency_p95_ms,
            notes=f"Split: {summary.split}, Items: {summary.item_count}",
        )

        with open(path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

        logger.info("Saved eval run record", run_id=record.run_id, path=str(path))
        return record
