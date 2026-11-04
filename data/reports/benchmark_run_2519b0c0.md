# Benchmark Report: `run_2519b0c0`

- **Split:** `train`
- **Items Evaluated:** 36
- **Config Hash:** `86fa89f9449408e3`
- **p50 Latency:** 1.36 ms
- **p95 Latency:** 1.81 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.0000 | — | — |
| Hit Rate@3 | 0.0000 | — | — |
| Hit Rate@5 | 0.0000 | ≥ 0.8500 | FLAG |
| Hit Rate@10 | 0.0000 | — | — |
| MRR | 0.0000 | ≥ 0.6500 | FLAG |
| Faithfulness | 0.9661 | ≥ 0.9000 | PASS |
| Correctness | 0.1607 | — | — |
| Completeness | 0.1589 | — | — |
| Mean Semantic Sim | 0.1396 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_01` | factoid | What encryption algorithm is used to protect ... | 0.02 | 0.88 | 0.07 | 45.13 |
| `gold_fact_02` | factoid | Which availability zones does the Acme Cloud ... | 0.00 | 1.00 | 0.00 | 1.81 |
| `gold_fact_03` | factoid | What protocol and tool must remote employees ... | 0.00 | 1.00 | 0.00 | 1.62 |
| `gold_fact_05` | factoid | What type of token is required for all Acme A... | 0.00 | 1.00 | 0.00 | 1.39 |
| `gold_fact_07` | factoid | Where must all incident post-mortems be publi... | 0.00 | 1.00 | 0.00 | 1.31 |
| `gold_fact_08` | factoid | What screen lock and disk encryption standard... | 0.00 | 1.00 | 0.00 | 1.66 |
| `gold_fact_09` | factoid | What status code is returned when API rate li... | 0.00 | 1.00 | 0.00 | 1.51 |
| `gold_fact_10` | factoid | What format header is returned prior to decom... | 0.00 | 1.00 | 0.00 | 1.32 |
| `gold_fact_12` | factoid | Which email address must employees use to rep... | 0.00 | 1.00 | 0.00 | 1.25 |
| `gold_fact_13` | factoid | When do scheduled infrastructure maintenance ... | 0.00 | 1.00 | 0.00 | 1.47 |
