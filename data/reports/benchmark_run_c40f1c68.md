# Benchmark Report: `run_c40f1c68`

- **Split:** `holdout`
- **Items Evaluated:** 16
- **Config Hash:** `86fa89f9449408e3`
- **p50 Latency:** 9.46 ms
- **p95 Latency:** 96.36 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.6923 | — | — |
| Hit Rate@3 | 0.9231 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.8103 | >= 0.6500 | PASS |
| Faithfulness | 0.9500 | >= 0.9000 | PASS |
| Correctness | 0.5619 | — | — |
| Completeness | 0.5858 | — | — |
| Mean Semantic Sim | 0.5323 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_04` | factoid | What authentication mechanism is strictly man... | 0.80 | 1.00 | 0.89 | 96.36 |
| `gold_fact_06` | factoid | How is revoked API key propagation communicat... | 0.91 | 1.00 | 1.00 | 9.46 |
| `gold_fact_11` | factoid | What type of primary storage does Acme Cloud ... | 0.00 | 1.00 | 0.00 | 10.4 |
| `gold_fact_14` | factoid | What is the emergency escalation telephone nu... | 0.92 | 1.00 | 1.00 | 9.04 |
| `gold_num_04` | numeric | What is the disaster recovery RTO and RPO tar... | 0.72 | 1.00 | 0.88 | 9.65 |
| `gold_num_07` | numeric | What was Acme's Annual Recurring Revenue (ARR... | 0.92 | 1.00 | 1.00 | 10.99 |
| `gold_multi_02` | multi_sentence | What hardware monitors, laptop, and accessori... | 0.50 | 1.00 | 0.47 | 11.48 |
| `gold_multi_04` | multi_sentence | What are the rate limit tiers for Developer, ... | 0.00 | 1.00 | 0.00 | 8.82 |
| `gold_multi_05` | multi_sentence | Explain the working hours and daily standup c... | 0.73 | 1.00 | 0.65 | 10.21 |
| `gold_multi_06` | multi_sentence | What are the rules and pagination limits for ... | 0.68 | 1.00 | 0.76 | 8.77 |
