# Benchmark Report: `run_acf6fce1`

- **Split:** `holdout`
- **Items Evaluated:** 16
- **Config Hash:** `6e2f06b18998d97f`
- **p50 Latency:** 6.4 ms
- **p95 Latency:** 22.66 ms

## Summary Metrics

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| Hit Rate@1 | 0.3846 | — | — |
| Hit Rate@3 | 0.7692 | — | — |
| Hit Rate@5 | 1.0000 | >= 0.8500 | PASS |
| Hit Rate@10 | 1.0000 | — | — |
| MRR | 0.6051 | >= 0.6500 | FLAG |
| Faithfulness | 1.0000 | >= 0.9000 | PASS |
| Correctness | 0.3934 | — | — |
| Completeness | 0.4112 | — | — |
| Mean Semantic Sim | 0.3828 | — | — |

## Per-Item Results Preview (First 10)

| Item ID | Type | Question | Sim | Faith | Corr | Total (ms) |
|---|---|---|---|---|---|---|
| `gold_fact_04` | factoid | What authentication mechanism is strictly man... | 0.80 | 1.00 | 0.89 | 22.66 |
| `gold_fact_06` | factoid | How is revoked API key propagation communicat... | 0.00 | 1.00 | 0.00 | 10.96 |
| `gold_fact_11` | factoid | What type of primary storage does Acme Cloud ... | 0.04 | 1.00 | 0.07 | 6.53 |
| `gold_fact_14` | factoid | What is the emergency escalation telephone nu... | 0.00 | 1.00 | 0.00 | 5.9 |
| `gold_num_04` | numeric | What is the disaster recovery RTO and RPO tar... | 0.72 | 1.00 | 0.88 | 6.1 |
| `gold_num_07` | numeric | What was Acme's Annual Recurring Revenue (ARR... | 0.00 | 1.00 | 0.00 | 6.21 |
| `gold_multi_02` | multi_sentence | What hardware monitors, laptop, and accessori... | 0.50 | 1.00 | 0.47 | 6.3 |
| `gold_multi_04` | multi_sentence | What are the rate limit tiers for Developer, ... | 0.00 | 1.00 | 0.00 | 6.47 |
| `gold_multi_05` | multi_sentence | Explain the working hours and daily standup c... | 0.73 | 1.00 | 0.65 | 6.4 |
| `gold_multi_06` | multi_sentence | What are the rules and pagination limits for ... | 0.00 | 1.00 | 0.00 | 7.49 |
