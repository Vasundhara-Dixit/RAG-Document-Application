# Rules: Engineering & AI-Agent Conventions

> **MEMORY RULE (mandatory, highest priority):** `memory.md` is the project's persistent brain. EVERY session, the AI must: (1) read `memory.md`, `phases.md`, then relevant docs BEFORE acting; (2) after each completed task/experiment/decision, update `memory.md`; (3) if `memory.md` does not exist, create it from its template. Work is not "done" until memory is updated.

## 1. AI Agent Workflow
1. Read `memory.md` → find current phase and next steps.
2. Check task against `PRD.md` (FR-ID) and `Architecture.md`. Don't invent scope; propose changes instead.
3. Plan briefly, implement the smallest working slice, test, then evaluate (if retrieval/generation touched).
4. Update: `memory.md` (always), `phases.md` checkboxes, `Architecture.md` ADR (if structural), `design.md` (if UI).
5. Never claim tests/benchmarks passed unless actually run; paste real numbers into `memory.md`.
6. Ask the user only when a decision changes architecture, cost, or scope (max 3 questions); otherwise decide, and log the assumption.
7. **Token economy:** read only files needed; prefer diffs/targeted edits over rewriting files; keep responses concise; don't repeat doc contents.

## 2. Code Standards (Python)
- Python 3.11+, full type hints, `ruff` + `black` + `mypy --strict` on `app/`.
- Pydantic models for config, API schemas, and data records. No magic numbers; read from `config.yaml`.
- One responsibility per module; stages implement the abstract interfaces in `app/core/interfaces.py`.
- No global mutable state; dependency injection via constructors/FastAPI `Depends`.
- Functions ≤ 50 lines; docstrings on public APIs (Google style).
- Async only at API/IO boundaries; CPU work (embedding, parsing) in worker threads/processes.
- Deterministic: seed everything; pin dependency versions (`uv`/`pip-tools` lockfile).
- Logging via `structlog`/`logging` JSON; never `print`. No document text above DEBUG.

## 3. RAG-Specific Rules
1. **No retrieval/chunking/prompt/model change without a benchmark run** before and after; log both in `memory.md`.
2. Chunking: size 256–1024 tokens, overlap 10–20% unless an experiment justifies otherwise; never split mid-sentence if avoidable; keep page/offset metadata.
3. Always L2-normalize embeddings when using inner product. Store `embedding_model` + `config_hash` per chunk; re-embed on model change (never mix models in one index).
4. Generation must be grounded: answer only from context, cite sources, abstain when unsupported. Test abstention explicitly.
5. Treat retrieved text as untrusted (prompt injection): delimit it, never execute instructions inside it.
6. Never tune on the hold-out split. Golden set changes are versioned; never silently edit.
7. LLM-judge: pinned model/version, fixed rubric, temperature 0, JSON output; manually spot-check ≥10%.
8. Keep an enhancement only if it improves a primary metric by a meaningful margin relative to latency/cost (record the trade-off).
9. Every ingestion is idempotent (checksum); deletions remove vectors from both FAISS and Chroma.

## 4. Testing
| Level | Scope | Rule |
|---|---|---|
| Unit | parsers, cleaner, chunker, metrics (Hit@K, MRR on hand-computed cases) | required for every module |
| Integration | ingest → retrieve → answer on a tiny fixture corpus | required per phase |
| Eval | golden set benchmark | required on retrieval/prompt/model change |
| Regression (Phase 8) | Ragas thresholds in CI | block merge on drop > threshold |
- Fixtures live in `tests/fixtures`; no network calls in unit tests (mock LLM/embedder).
- Coverage ≥ 80% on `app/` core.

## 5. Git & Process
- Branches: `feat/<fr-id>-name`, `fix/…`, `exp/<name>` (experiments). Conventional commits (`feat:`, `fix:`, `docs:`, `exp:`).
- Small PRs (< 400 lines). PR must reference FR-ID, include eval table if RAG behavior changed.
- Never commit secrets, data under `data/raw`, or index files (`.gitignore`). Provide `.env.example`.

## 6. Security & Privacy
- Validate uploads (extension + magic bytes, max size from config); sanitize filenames; store by `doc_id`.
- Secrets only via environment; never in code, logs, or `memory.md`.
- Don't send documents to third-party APIs unless config `allow_external_llm: true`; document the choice in `memory.md`.
- Redact PII in logs; guardrails added in Phase 7.

## 7. API & Error Rules
- Version routes (`/v1`); consistent error schema `{code, message, detail}`.
- Timeouts + retries (exponential backoff) on LLM/embedding calls; surface partial failures.
- Every response includes `trace_id`; every `/query` returns citations and timings.

## 8. Frontend Rules
Follow `design.md` strictly: use tokens (no raw hex in components), meet WCAG 2.2 AA, honor `prefers-reduced-motion`, cover loading/empty/error/success states. No new UI dependency without justification logged in `memory.md`.

## 9. Documentation Rules
- Docs are source of truth; update in the same PR as the code change.
- Record every non-trivial decision as ADR (`docs/ADR/NNN-title.md`) + row in `Architecture.md`.
- Experiments logged as: config → metrics → conclusion (in `memory.md` experiments table).

## 10. Definition of Done
Code typed & linted · tests pass · benchmark run (if RAG-affecting) · docs updated · **`memory.md` updated** · `phases.md` checkbox ticked.
