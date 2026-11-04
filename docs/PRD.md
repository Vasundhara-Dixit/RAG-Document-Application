# PRD: RAG Document Q&A Application
Version 1.0 · Status: Draft · Owner: Project lead

> **AI AGENT RULE (memory):** Before starting and after finishing ANY task, read and then update `memory.md` (state, decisions, experiments, eval results, issues, next steps). If `memory.md` is missing, create it from the template in that file. Never end a session without updating it.

## 1. Overview
An evaluation-driven Retrieval-Augmented Generation (RAG) system that lets users ask natural-language questions over private, unstructured document collections (PDF, DOCX, MD, TXT) and receive answers grounded in, and cited to, those documents. RAG is treated as an engineering discipline: chunking, indexing and retrieval are tuned empirically and measured against a curated golden test set (Hit Rate@K, MRR, faithfulness), not assumed to work.

## 2. Problem & Goals
**Problem:** Teams cannot quickly find reliable answers in private documents; generic LLMs hallucinate and cannot see private data; naive RAG is rarely measured.

| # | Goal | Measure |
|---|---|---|
| G1 | Accurate grounded answers | Faithfulness ≥ 0.90 (LLM-judge) on golden set |
| G2 | High retrieval quality | Hit Rate@5 ≥ 0.85, MRR ≥ 0.65 (baseline, then improve) |
| G3 | Trustworthy | Every answer shows citations (doc + page); "I don't know" when context lacks answer |
| G4 | Reproducible tuning | Every config change has logged eval before/after (in `memory.md`) |
| G5 | Responsive | p95 retrieval < 300 ms; time-to-first-token < 2 s |

**Non-goals (v1):** multimodal/OCR, RBAC, multi-tenant SaaS, fine-tuning models, agentic web browsing.

## 3. Personas
- **Analyst (primary):** uploads reports, asks specific questions, needs citations to verify.
- **Engineer/Support:** searches manuals, error codes, product models (needs exact-match later → hybrid).
- **Maintainer (ML/dev):** tunes chunking/retrieval, runs benchmarks, compares configs.

## 4. Scope Tiers
- **Tier 1 – Implemented/MVP:** parsing, tuned chunking, embeddings, FAISS + ChromaDB, k-NN retrieval, context-injected generation, Hit Rate/MRR benchmark, answer-quality evaluation.
- **Tier 2 – Retrieval enhancements:** hybrid BM25+dense (RRF), cross-encoder rerank, small-to-big, contextual chunk enrichment, query transformation (HyDE, multi-query, step-back).
- **Tier 3 – Ingestion:** layout/table parsing, OCR + multimodal, incremental updates via checksums.
- **Tier 4 – UX/agentic:** multi-turn memory, clickable citations + PDF highlight, CRAG + web fallback, multi-hop decomposition, streaming + guardrails.
- **Tier 5 – Enterprise:** RBAC, semantic cache, CI/CD eval regression, tracing.

## 5. Functional Requirements
Priority: P0 must, P1 should, P2 could. Phase refs → `phases.md`.

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| FR-01 | Upload PDF/DOCX/MD/TXT; reject unsupported/oversized files with clear error | P0 | 1 |
| FR-02 | Extract clean text; strip headers/footers, layout artifacts, excess whitespace; keep page numbers | P0 | 1 |
| FR-03 | Configurable chunking (size 256–1024 tokens, overlap 10–20%), sentence-boundary aware; chunk metadata (doc_id, page, chunk_idx, offsets) | P0 | 2 |
| FR-04 | Embed chunks (configurable model) and persist in FAISS (search) + ChromaDB (persistence/metadata) | P0 | 2 |
| FR-05 | Top-k retrieval by cosine/inner product with metadata filters | P0 | 3 |
| FR-06 | Generation with retrieved context in structured system prompt; answer only from context; refuse if insufficient | P0 | 3 |
| FR-07 | Return citations (doc name, page, snippet) with each answer | P0 | 3 |
| FR-08 | Golden QA set management (CRUD, versioned) | P0 | 4 |
| FR-09 | Retrieval benchmark: Hit Rate@K (K=1,3,5,10), MRR; per-config report | P0 | 4 |
| FR-10 | Answer evaluation: semantic similarity + LLM-as-judge (faithfulness, correctness, completeness) | P0 | 4 |
| FR-11 | Experiment runner comparing chunk size/overlap/embedder/index configs | P1 | 4 |
| FR-12 | Web UI: upload, library, chat, citations, eval dashboard | P0 | 5 |
| FR-13 | Hybrid BM25 + dense with RRF | P1 | 6 |
| FR-14 | Cross-encoder rerank (top-50 → top 3–5) | P1 | 6 |
| FR-15 | Small-to-big retrieval; contextual chunk enrichment | P1 | 6 |
| FR-16 | Query transformation (HyDE, multi-query, step-back) | P2 | 6 |
| FR-17 | Structured table parsing; OCR; multimodal | P2 | 7 |
| FR-18 | Incremental indexing (checksum dedupe, delta updates/deletes) | P1 | 7 |
| FR-19 | Multi-turn memory (query condensation) | P1 | 7 |
| FR-20 | PDF viewer with highlighted source box | P2 | 7 |
| FR-21 | CRAG + web fallback; multi-hop decomposition | P2 | 7 |
| FR-22 | Streaming + guardrails (PII mask, out-of-scope reject) | P1 | 7 |
| FR-23 | RBAC via metadata pre-filtering | P2 | 8 |
| FR-24 | Semantic cache | P2 | 8 |
| FR-25 | CI eval regression (Ragas/TruLens/DeepEval) | P1 | 8 |
| FR-26 | Tracing: latency, tokens, retrieval quality, feedback (Langfuse/Phoenix/OTel) | P1 | 8 |

## 6. Non-Functional Requirements
- **Performance:** p95 retrieval < 300 ms at 100k chunks; ingestion ≥ 20 pages/s (text PDFs).
- **Reliability:** idempotent ingestion; index rebuildable from stored source docs.
- **Security/Privacy:** documents stay local/private; secrets in env; no document text in logs at INFO; PII guardrails (Phase 7).
- **Reproducibility:** every eval run stores config hash, dataset version, model versions, seed.
- **Maintainability:** typed Python, ≥ 80% unit coverage on core pipeline.
- **Accessibility:** WCAG 2.2 AA UI (see `design.md`).

## 7. Success Metrics
| Metric | Definition |
|---|---|
| Hit Rate@K | % queries whose ground-truth doc/chunk is in top-K |
| MRR | mean(1/rank of first relevant result) |
| Faithfulness | % answer claims supported by retrieved context |
| Answer correctness | judge/similarity score vs reference answer |
| Latency / cost | p50/p95 end-to-end; tokens per query |

Golden set: ≥ 50 QA pairs for MVP (≥ 150 later), covering factoid, multi-sentence, numeric, no-answer and ambiguous questions; each item has `question, reference_answer, source_doc, source_chunk/page`.

## 8. Key Risks
| Risk | Mitigation |
|---|---|
| Golden set too small/biased | Mix manual + LLM-drafted, human-reviewed; version it |
| LLM-judge bias/drift | Pin judge model; spot-check 10% manually |
| Tuning to the test set | Hold-out split (70/30) |
| Cost/latency from rerank/HyDE | Measure each enhancement; keep only if gain justifies cost |

## 9. Open Questions
LLM/embedding provider (API vs local)? Max corpus size? Auth needed in v1? → record answers in `memory.md` decisions log.
