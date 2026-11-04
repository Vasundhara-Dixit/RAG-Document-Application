# ADR-004: Hold-out Split for Golden Test Set

## Status
Accepted

## Context
When tuning retrieval parameters (e.g. chunk size, overlap ratio, BM25 weight, reranker top-k) or prompt instructions, evaluating on the entire test set leads to data leakage and overfitting to specific questions.

## Decision
The Golden QA Set will enforce a strict 70% `train` / 30% `holdout` partition marked by the `split` field in `GoldenItem`.
- The experiment grid runner and automated hyperparameter sweeps will evaluate only against the `train` split.
- The `holdout` split will only be used for release verification and CI regression checks.

## Consequences
- Prevents over-optimizing retrieval thresholds on idiosyncratic queries.
- Ensures generalization on novel documents and queries.

