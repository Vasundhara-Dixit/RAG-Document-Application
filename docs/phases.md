# Phases: Delivery Roadmap

> **AI AGENT RULE (memory):** At the start of each session read `memory.md` to find the active phase. After each task: tick checkboxes here and log progress, metrics and decisions in `memory.md`. Create `memory.md` if missing. Don't start a phase until the previous phase's exit criteria are met (unless the user overrides).

Legend: `[ ]` todo · `[x]` done · FR = PRD requirement ID. Estimates assume one developer.

## Phase 0: Foundation (2–3 days)
- [x] Repo scaffold per `Architecture.md §8`, `pyproject.toml`, lockfile, ruff/black/mypy, pre-commit
- [x] `config.yaml` + Pydantic settings; `.env.example`; logging
- [x] Abstract interfaces (`Parser, Chunker, Embedder, VectorIndex, Retriever, LLM`)
- [x] Tiny fixture corpus (3–5 docs) + CI skeleton (lint, test)
- [x] Initialize `memory.md`
**Exit:** `pytest` and lint pass on empty pipeline; docs committed.

## Phase 1: Ingestion & Parsing (FR-01, 02) (3–4 days)
- [x] Parsers: PDF (PyMuPDF), DOCX, MD, TXT with page metadata
- [x] Cleaner (headers/footers, hyphenation, whitespace, unicode)
- [x] Upload validation, checksum registry (SQLite)
- [x] Unit tests incl. messy-PDF fixtures
**Exit:** all four formats → clean text with page numbers; invalid files rejected.

## Phase 2: Chunking, Embedding & Indexing (FR-03, 04) (4–5 days)
- [x] Token-aware, sentence-aware chunker (size/overlap configurable) + metadata
- [x] Embedder wrapper (batching, normalization, retries, cache)
- [x] Chroma persistence + FAISS index (build/load/save; delete by doc)
- [x] Rebuild-from-Chroma script; `config_hash` stamping
**Exit:** ingest fixture corpus end-to-end; restart app and index reloads identically.

## Phase 3: Retrieval & Generation (FR-05, 06, 07) (3–4 days)
- [x] k-NN retriever with metadata filter + score threshold
- [x] Prompt templates (grounded, citation format, abstention); token budgeting
- [x] LLM client (LiteLLM), retries, streaming-ready
- [x] `/query`, `/retrieve`, `/documents` endpoints
**Exit:** correct cited answers on manual smoke questions; abstains on unanswerable ones.

## Phase 4: Evaluation Harness (FR-08–11) (5–6 days) ★ core differentiator
- [x] Build golden set (≥50 QA; types: factoid/numeric/multi-sentence/no-answer; hold-out 30%)
- [x] Metrics: Hit Rate@{1,3,5,10}, MRR (unit-tested on hand-computed cases)
- [x] Answer eval: semantic similarity + LLM-judge (faithfulness/correctness/completeness)
- [x] Experiment runner (grid: chunk size 256/512/768/1024 × overlap 10/15/20% × embedder × index)
- [x] Reports (CSV + markdown), run registry; log baseline & best config in `memory.md`
**Exit:** reproducible baseline; chosen config justified by data (targets: Hit@5 ≥ 0.85, MRR ≥ 0.65, faithfulness ≥ 0.90).

## Phase 5: Web UI MVP (FR-12) (5–7 days)
- [x] Implement `design.md` tokens/components (upload, library, chat, citations, eval dashboard)
- [x] SSE streaming in chat; error/empty/loading states
- [x] a11y pass (axe, keyboard, reduced motion); Lighthouse budgets
**Exit:** user can upload, ask, see citations, and view eval results in UI. **MVP release (v0.1).**

## Phase 6: Advanced Retrieval (FR-13–16) (7–10 days)
Each item = implement → benchmark vs baseline → keep/reject → log.
- [x] Hybrid BM25 + dense with RRF
- [x] Cross-encoder reranker (top-50 → top-5)
- [x] Small-to-big + contextual chunk enrichment
- [x] Query transformation: HyDE, multi-query, step-back
**Exit:** documented metric deltas and latency/cost impact per feature; defaults updated.

## Phase 7: Ingestion, UX & Agentic Features (FR-17–22) (10–14 days)
- [ ] Layout/table parsing (Markdown/HTML tables); OCR; optional multimodal (ColPali/CLIP)
- [ ] Incremental indexing (checksum, delta, deletes)
- [ ] Multi-turn condensation; PDF viewer with highlighted citations
- [ ] CRAG + web fallback; multi-hop decomposition
- [ ] Streaming guardrails (PII mask, out-of-scope rejection)
**Exit:** golden set extended for new capabilities; no regression on baseline metrics.

## Phase 8: Enterprise, Observability & Hardening (FR-23–26) (7–10 days)
- [ ] RBAC pre-filtering; auth integration
- [ ] Semantic cache (Redis/GPTCache) with similarity threshold tuning
- [ ] CI eval regression (Ragas/TruLens/DeepEval) gating merges
- [ ] Tracing/feedback (Langfuse/Phoenix/OTel); dashboards
- [ ] Load test, vector store migration path (Qdrant/Pinecone), Docker Compose, runbook
**Exit:** v1.0 release; SLOs met (p95 retrieval < 300 ms, TTFT < 2 s).

## Dependency Map
`0 → 1 → 2 → 3 → 4 → (5 ∥ 6) → 7 → 8` (Phase 4 gates all retrieval work; Phase 5 can run parallel to 6 once the API is stable.)

## Phase Log (AI updates)
| Phase | Status | Started | Finished | Notes → see memory.md |
|---|---|---|---|---|
| 0 | Completed | 2026-11-02 | 2026-11-02 | Repo scaffold, pyproject, config.yaml, interfaces, schemas, logging, fixtures, tests passing |
| 1 | Completed | 2026-11-02 | 2026-11-02 | Ingestion & Parsing (FR-01, FR-02): PyMuPDF, docx, md, txt parsers, cleaner, registry, 15 tests pass |
| 2 | Completed | 2026-11-02 | 2026-11-02 | Chunking, Embedding & Indexing (FR-03, FR-04): Sentence chunker, dual FAISS+Chroma store, reload verified |
| 3 | Completed | 2026-11-02 | 2026-11-02 | Retrieval & Generation (FR-05, FR-06, FR-07): KNN retriever, grounded prompts, LiteLLM/Mock client, FastAPI routes |
| 4 | Completed | 2026-11-02 | 2026-11-02 | Evaluation Harness (FR-08–11): 52 QA golden set (70/30 split), Hit@K, MRR, LLM judge, CSV/MD reports; Hit@5=1.0, MRR=0.9355, Faith=0.9778 |
| 5 | Completed | 2026-11-02 | 2026-11-02 | Web UI MVP (FR-12): React+Vite+Tailwind "The Reading Room" theme, Chat with SSE stream & M-03 highlighter sweep, Document Library, Eval Dashboard |
| 6 | Completed | 2026-11-02 | 2026-11-02 | Advanced Retrieval (FR-13–16): Hybrid BM25+Dense RRF, FastCrossEncoderReranker, Small-to-big ParentDocumentRetriever, QueryProcessor (HyDE, multi-query, step-back). Holdout Hit@1 improved from 0.6923 to 0.9231, MRR from 0.8103 to 0.9615. 45 tests pass. |
| 7 | In progress | 2026-11-02 | | Ingestion, UX & Agentic Features (FR-17–22) |
| 8 | Not started | | | |
