# Benchmark Report: `run_80f52da7`

- **Split:** `train`
- **Items Evaluated:** 2
- **Config Hash:** `6e2f06b18998d97f`
- **p50 Latency:** 3.06 ms
- **p95 Latency:** 3.06 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.0000 | — | — |
| Hit Rate@3 | 0.0000 | — | — |
| Hit Rate@5 | 0.0000 | >= 0.8500 | FLAG |
| Hit Rate@10 | 0.0000 | — | — |
| MRR | 0.0000 | >= 0.6500 | FLAG |
| Faithfulness | 1.0000 | >= 0.9000 | PASS |
| Correctness | 0.9285 | — | — |
| Completeness | 1.0000 | — | — |
| Mean Semantic Sim | 0.8847 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `eval_q1` | factoid | When do nightly backups execute? | 0.77 | 1.00 | 0.86 | 3.06 |
| `eval_q2` | no_answer | What is the lunch menu for the cafeteria? | 1.00 | 1.00 | 1.00 | 2.39 |
