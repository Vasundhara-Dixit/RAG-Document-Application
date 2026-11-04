# Benchmark Report: `run_700e9d14`

- **Split:** `train`
- **Items Evaluated:** 36
- **Config Hash:** `86fa89f9449408e3`
- **p50 Latency:** 1.81 ms
- **p95 Latency:** 3.37 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.2903 | — | — |
| Hit Rate@3 | 0.5484 | — | — |
| Hit Rate@5 | 0.7742 | >= 0.8500 | FLAG |
| Hit Rate@10 | 0.7742 | — | — |
| MRR | 0.4478 | >= 0.6500 | FLAG |
| Faithfulness | 0.9215 | >= 0.9000 | PASS |
| Correctness | 0.2909 | — | — |
| Completeness | 0.3517 | — | — |
| Mean Semantic Sim | 0.0873 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_01` | factoid | What encryption algorithm is used to protect ... | 0.00 | 1.00 | 0.00 | 53.96 |
| `gold_fact_02` | factoid | Which availability zones does the Acme Cloud ... | 0.05 | 0.92 | 0.61 | 2.44 |
| `gold_fact_03` | factoid | What protocol and tool must remote employees ... | 0.00 | 1.00 | 0.00 | 2.0 |
| `gold_fact_05` | factoid | What type of token is required for all Acme A... | 0.00 | 1.00 | 0.00 | 1.98 |
| `gold_fact_07` | factoid | Where must all incident post-mortems be publi... | 0.03 | 0.88 | 0.90 | 1.98 |
| `gold_fact_08` | factoid | What screen lock and disk encryption standard... | 0.00 | 0.88 | 0.86 | 1.81 |
| `gold_fact_09` | factoid | What status code is returned when API rate li... | 0.00 | 0.91 | 0.17 | 1.93 |
| `gold_fact_10` | factoid | What format header is returned prior to decom... | 0.01 | 0.87 | 0.85 | 3.37 |
| `gold_fact_12` | factoid | Which email address must employees use to rep... | 0.00 | 1.00 | 0.00 | 1.97 |
| `gold_fact_13` | factoid | When do scheduled infrastructure maintenance ... | 0.05 | 0.89 | 0.73 | 1.99 |
