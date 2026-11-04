# Benchmark Report: `run_e2fc6c89`

- **Split:** `train`
- **Items Evaluated:** 36
- **Config Hash:** `6e2f06b18998d97f`
- **p50 Latency:** 3.82 ms
- **p95 Latency:** 5.0 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.9032 | — | — |
| Hit Rate@3 | 0.9677 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.9435 | >= 0.6500 | PASS |
| Faithfulness | 0.9556 | >= 0.9000 | PASS |
| Correctness | 0.6189 | — | — |
| Completeness | 0.7020 | — | — |
| Mean Semantic Sim | 0.6010 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_01` | factoid | What encryption algorithm is used to protect ... | 0.73 | 1.00 | 0.71 | 15.07 |
| `gold_fact_02` | factoid | Which availability zones does the Acme Cloud ... | 0.19 | 1.00 | 0.43 | 3.82 |
| `gold_fact_03` | factoid | What protocol and tool must remote employees ... | 0.74 | 1.00 | 0.83 | 4.16 |
| `gold_fact_05` | factoid | What type of token is required for all Acme A... | 0.23 | 1.00 | 0.29 | 3.68 |
| `gold_fact_07` | factoid | Where must all incident post-mortems be publi... | 0.92 | 1.00 | 1.00 | 3.4 |
| `gold_fact_08` | factoid | What screen lock and disk encryption standard... | 0.88 | 1.00 | 0.96 | 3.95 |
| `gold_fact_09` | factoid | What status code is returned when API rate li... | 0.27 | 1.00 | 0.19 | 3.65 |
| `gold_fact_10` | factoid | What format header is returned prior to decom... | 0.87 | 1.00 | 0.96 | 3.54 |
| `gold_fact_12` | factoid | Which email address must employees use to rep... | 0.86 | 1.00 | 0.97 | 3.77 |
| `gold_fact_13` | factoid | When do scheduled infrastructure maintenance ... | 0.82 | 1.00 | 0.81 | 3.54 |
