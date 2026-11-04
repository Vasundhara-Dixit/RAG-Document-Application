# Benchmark Report: `run_8ad6794d`

- **Split:** `holdout`
- **Items Evaluated:** 16
- **Config Hash:** `6e2f06b18998d97f`
- **p50 Latency:** 3.53 ms
- **p95 Latency:** 16.93 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.8462 | — | — |
| Hit Rate@3 | 0.9231 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.9038 | >= 0.6500 | PASS |
| Faithfulness | 0.9500 | >= 0.9000 | PASS |
| Correctness | 0.6409 | — | — |
| Completeness | 0.6678 | — | — |
| Mean Semantic Sim | 0.6062 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_04` | factoid | What authentication mechanism is strictly man... | 0.80 | 1.00 | 0.89 | 16.93 |
| `gold_fact_06` | factoid | How is revoked API key propagation communicat... | 0.91 | 1.00 | 1.00 | 3.39 |
| `gold_fact_11` | factoid | What type of primary storage does Acme Cloud ... | 0.00 | 1.00 | 0.00 | 3.53 |
| `gold_fact_14` | factoid | What is the emergency escalation telephone nu... | 0.92 | 1.00 | 1.00 | 3.87 |
| `gold_num_04` | numeric | What is the disaster recovery RTO and RPO tar... | 0.72 | 1.00 | 0.88 | 3.65 |
| `gold_num_07` | numeric | What was Acme's Annual Recurring Revenue (ARR... | 0.92 | 1.00 | 1.00 | 3.45 |
| `gold_multi_02` | multi_sentence | What hardware monitors, laptop, and accessori... | 0.50 | 1.00 | 0.47 | 3.51 |
| `gold_multi_04` | multi_sentence | What are the rate limit tiers for Developer, ... | 0.27 | 1.00 | 0.29 | 3.64 |
| `gold_multi_05` | multi_sentence | Explain the working hours and daily standup c... | 0.73 | 1.00 | 0.65 | 3.39 |
| `gold_multi_06` | multi_sentence | What are the rules and pagination limits for ... | 0.68 | 1.00 | 0.76 | 3.5 |
