# Benchmark Report: `run_0524d2d9`

- **Split:** `train`
- **Items Evaluated:** 36
- **Config Hash:** `6e2f06b18998d97f`
- **p50 Latency:** 3.55 ms
- **p95 Latency:** 4.77 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.8710 | — | — |
| Hit Rate@3 | 1.0000 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.9355 | >= 0.6500 | PASS |
| Faithfulness | 0.9778 | >= 0.9000 | PASS |
| Correctness | 0.6458 | — | — |
| Completeness | 0.7242 | — | — |
| Mean Semantic Sim | 0.6275 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_01` | factoid | What encryption algorithm is used to protect ... | 0.73 | 1.00 | 0.71 | 15.58 |
| `gold_fact_02` | factoid | Which availability zones does the Acme Cloud ... | 0.19 | 1.00 | 0.43 | 4.77 |
| `gold_fact_03` | factoid | What protocol and tool must remote employees ... | 0.74 | 1.00 | 0.83 | 3.89 |
| `gold_fact_05` | factoid | What type of token is required for all Acme A... | 0.23 | 1.00 | 0.29 | 3.53 |
| `gold_fact_07` | factoid | Where must all incident post-mortems be publi... | 0.92 | 1.00 | 1.00 | 2.94 |
| `gold_fact_08` | factoid | What screen lock and disk encryption standard... | 0.88 | 1.00 | 0.96 | 3.83 |
| `gold_fact_09` | factoid | What status code is returned when API rate li... | 0.27 | 1.00 | 0.19 | 3.45 |
| `gold_fact_10` | factoid | What format header is returned prior to decom... | 0.87 | 1.00 | 0.96 | 3.68 |
| `gold_fact_12` | factoid | Which email address must employees use to rep... | 0.86 | 1.00 | 0.97 | 3.82 |
| `gold_fact_13` | factoid | When do scheduled infrastructure maintenance ... | 0.77 | 1.00 | 0.79 | 3.08 |
