# Benchmark Report: `run_a9e9b124`

- **Split:** `train`
- **Items Evaluated:** 36
- **Config Hash:** `86fa89f9449408e3`
- **p50 Latency:** 8.28 ms
- **p95 Latency:** 48.9 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.8710 | — | — |
| Hit Rate@3 | 1.0000 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.9355 | >= 0.6500 | PASS |
| Faithfulness | 0.8993 | >= 0.9000 | FLAG |
| Correctness | 0.5995 | — | — |
| Completeness | 0.7272 | — | — |
| Mean Semantic Sim | 0.6275 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_01` | factoid | What encryption algorithm is used to protect ... | 0.73 | 0.92 | 0.65 | 103.54 |
| `gold_fact_02` | factoid | Which availability zones does the Acme Cloud ... | 0.19 | 0.90 | 0.39 | 8.26 |
| `gold_fact_03` | factoid | What protocol and tool must remote employees ... | 0.74 | 0.88 | 0.74 | 48.9 |
| `gold_fact_05` | factoid | What type of token is required for all Acme A... | 0.23 | 0.87 | 0.25 | 10.32 |
| `gold_fact_07` | factoid | Where must all incident post-mortems be publi... | 0.92 | 0.88 | 0.90 | 7.74 |
| `gold_fact_08` | factoid | What screen lock and disk encryption standard... | 0.88 | 0.88 | 0.86 | 7.82 |
| `gold_fact_09` | factoid | What status code is returned when API rate li... | 0.27 | 0.91 | 0.17 | 8.3 |
| `gold_fact_10` | factoid | What format header is returned prior to decom... | 0.87 | 0.87 | 0.85 | 8.72 |
| `gold_fact_12` | factoid | Which email address must employees use to rep... | 0.86 | 0.89 | 0.88 | 7.74 |
| `gold_fact_13` | factoid | When do scheduled infrastructure maintenance ... | 0.77 | 0.89 | 0.73 | 8.01 |
