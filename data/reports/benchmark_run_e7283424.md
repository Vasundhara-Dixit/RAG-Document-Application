# Benchmark Report: `run_e7283424`

- **Split:** `train`
- **Items Evaluated:** 2
- **Config Hash:** `86fa89f9449408e3`
- **p50 Latency:** 2.65 ms
- **p95 Latency:** 2.65 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.5000 | — | — |
| Hit Rate@3 | 0.5000 | — | — |
| Hit Rate@5 | 0.5000 | ≥ 0.8500 | FLAG |
| Hit Rate@10 | 0.5000 | — | — |
| MRR | 0.5000 | ≥ 0.6500 | FLAG |
| Faithfulness | 0.7059 | ≥ 0.9000 | FLAG |
| Correctness | 0.7609 | — | — |
| Completeness | 1.0000 | — | — |
| Mean Semantic Sim | 0.5080 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `eval_q1` | factoid | When do nightly backups execute? | 0.02 | 0.41 | 0.52 | 2.65 |
| `eval_q2` | no_answer | What is the lunch menu for the cafeteria? | 1.00 | 1.00 | 1.00 | 1.7 |
