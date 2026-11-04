# memory.md: Persistent Project Memory

> **FOR THE AI:** Read this file FIRST every session; update it LAST every session. Keep it concise (summarize/compress old entries; never delete decisions). Create this file if missing. Never store secrets or document contents here.

## 1. Current State (overwrite each session)
- **Active phase:** 7 – Ingestion, UX & Agentic Features (FR-17–22)
- **Last session:** 2026-11-04 · Completed full visual frontend redesign matching `stitch_the_reading_room` and the user's custom 6-color palette (`#FFBB94`, `#FB9590`, `#DC586D`, `#A33757`, `#852E4E`, `#4C1D3D`). Implemented:
  1. Horizontally centered archival composer (`max-w-[760px] mx-auto`) with hotkey ribbon.
  2. The "+" action button inside the chatbox: file upload & instant ingestion, indexed manuscript referencing, and past chat session referencing with dismissible visual chips.
  3. Full chat session history management with intelligent auto-titling (`frontend/src/utils/chatHistory.ts`), "+ New Inquiry" action, session switcher, and one-click restoration of entire message threads, citations, and retrieval ledgers.
  4. M-03 highlighter sweep source inspector with passage stepper (`1 of 5`), facsimile attestation, and keyboard shortcuts (`Alt`+`↑`/`↓`, `Esc`).
  5. Library manifest export (`.jsonl`), drag-and-drop dropzone with stage progress indicator, and document deletion modal.
  6. Retrieval benchmark dashboard with comparative Hit@K recall bars, latency profiling, and golden QA taxonomy explorer.
  7. Created comprehensive operational manual `docs/lost_cause/TESTING_AND_CAPABILITIES.md`.
  8. Implemented Glass Background & Profile Settings Modal (`frontend/src/components/SettingsModal.tsx`): Default Toothless & Light Fury glass artwork (`/backgrounds/default_glass.jpg`), option to remove background and return to clean paper (`#FDF9F6`), custom device wallpaper upload, blur and opacity controls, accessible from top-right and bottom-left profile avatars with full `localStorage` persistence.
- **Branch / commit:** main / local
- **Active config hash:** 6e2f06b18998d97f
- **Blocked on:** none

## 2. Next Steps (ordered, max 7)
1. Implement structured table and layout parsing in `app/ingestion/parsers.py` (Markdown/HTML table extraction).
2. Implement incremental indexing with checksum delta verification and automated doc-level vector cleanup in `app/ingestion/registry.py`.
3. Implement multi-turn conversational query condensation in `app/generation/prompts.py` and `app/generation/memory.py`.
4. Integrate PDF viewer citation bounding box highlights with the frontend `SourceDrawer`.
5. Implement Corrective RAG (CRAG) confidence gating with web/fallback retrieval when internal context relevance is low.
6. Implement streaming guardrails (PII masking and out-of-scope query rejection).
7. Extend the golden test set with layout and multi-turn QA items, verify zero baseline regression, and update `memory.md`.

## 3. Project Facts (confirm & fill)
| Item | Value |
|---|---|
| Python version | 3.11.6 (virtualenv in `.venv`) |
| Tooling | pip, ruff, mypy, pytest, npm, vite, tailwindcss |
| LLM provider/model | LiteLLM (`gpt-4o-mini` default, mockable offline) |
| Embedding model | `text-embedding-3-small` (1536-dim, normalized) / mock embedder |
| Vector Index | FAISS `IndexFlatIP` (fast search) + ChromaDB (persistence/metadata) |
| Sparse Index | Okapi BM25 (in-memory, synchronized on ingestion/deletion) |
| Document Parsers | PyMuPDF (PDF), python-docx (DOCX), markdown-it-py (MD), text (TXT) |
| External APIs allowed? | Configurable via `allow_external_llm: false` (local fallback supported) |
| Target Corpus Types | PDF, DOCX, MD, TXT |
| Judge model (pinned) | `gpt-4o` (temperature 0.0, JSON rubric) |

## 4. Decisions Log (append-only)
| Date | Decision | Why | Alternatives | Ref (ADR/PR) |
|---|---|---|---|---|
| 2026-11-02 | FAISS search + Chroma persistence | Speed (<50ms ANN) + durable metadata storage | Chroma only, FAISS only | ADR-001 |
| 2026-11-02 | Pluggable interfaces for all pipeline stages | Decouples algorithms from vendor SDKs; enables drop-in Tier 2+ extensions | Monolithic pipeline | ADR-002 |
| 2026-11-02 | L2-normalize all embeddings | Allows FAISS IndexFlatIP inner product to equal cosine similarity | Inner product without normalization | ADR-003 |
| 2026-11-02 | Golden set 70/30 train/hold-out split | Prevents overfitting and data leakage during hyperparameter tuning | Single dataset | ADR-004 |
| 2026-11-02 | StrEnum for domain schema enums | Native Python 3.11 string enums compatible with Pydantic serialization and Ruff | `(str, Enum)` | PRD/Architecture |
| 2026-11-02 | PyMuPDF modern API migration | Replaced deprecated `fitz` import with `pymupdf` to eliminate deprecation warnings | `fitz` | Phase 1 |
| 2026-11-02 | Resilient offline tiktoken fallback | Avoids network download blocking when running in airgapped/sandboxed environments | Hard requirement on internet | Phase 2 |
| 2026-11-02 | Synchronous service layer & streaming | Avoids Windows sandbox asyncio socketpair deadlocks; Starlette threadpool handles sync endpoints natively | Async wrapping everywhere | Phase 3 |
| 2026-11-02 | Question substring extraction for Mock LLM | Prevents context text from triggering false positive keyword answers | Full prompt scan | Phase 3 |
| 2026-11-02 | Random Indexing Token Projection in MockEmbedder | Johnson-Lindenstrauss random projection yields semantically correlated vectors without external API keys | Orthogonal full-string hash | Phase 4 |
| 2026-11-02 | Strip citation brackets before claim tokenization | Prevents citations like `[doc, p.1]` from penalizing faithfulness scoring | Raw token match | Phase 4 |
| 2026-11-02 | Range-based multi-page retrieval matching | `page_start <= page_target <= page_end` accurately verifies multi-page chunks | Single page-start comparison | Phase 4 |
| 2026-11-02 | Production React SPA mounted in FastAPI | Serving Vite `dist/` directly from FastAPI root simplifies deployment into single container | Separate frontend server | Phase 5 |
| 2026-11-02 | Okapi BM25 with Reciprocal Rank Fusion (RRF, k=60) | Boosts exact technical keyword recall and elevates holdout Hit@1 from 0.6923 to 0.8462 | Dense-only, linear score interpolation | Phase 6 |
| 2026-11-02 | FastCrossEncoderReranker with query-passage term alignment | Computes cross-interaction features (coverage, phrase matching, span compactness) locally at ~1ms per item | Cloud-only reranker API | Phase 6 |
| 2026-11-02 | Hybrid + Cross-Encoder Reranker set as production default | Empirical superiority across all splits (Holdout Hit@1: 0.9231, MRR: 0.9615, Correctness: 0.7279) at 16ms p95 latency | Dense baseline | Phase 6 |
| 2026-11-02 | Reject Multi-Query and HyDE as defaults in offline mode | Without frontier LLM, synthetic variants introduce hallucinated noise that degrades MRR | Always-on transforms | Phase 6 |
| 2026-11-02 | Root `conftest.py` Faiss pre-import | Pre-loading Faiss before PyMuPDF prevents Windows OpenMP runtime DLL initialization collision | Disabling tests | Phase 6 |

## 5. Experiments Log
| ID | Date | Config (size/overlap/embedder/index/k) | Hit@1 | Hit@5 | MRR | Faith. | Latency p95 | Verdict |
|---|---|---|---|---|---|---|---|---|
| baseline-train | 2026-11-02 | 512/10%/MockProjection/IndexFlatIP/5/dense | 0.8710 | 1.0000 | 0.9355 | 0.9778 | 4.77 ms | PASS (baseline) |
| baseline-holdout | 2026-11-02 | 512/10%/MockProjection/IndexFlatIP/5/dense | 0.6923 | 1.0000 | 0.8103 | 0.9500 | 47.91 ms | PASS (baseline) |
| hybrid-train | 2026-11-02 | 512/10%/Dense+BM25/RRF k=60/k=5 | 0.8710 | 1.0000 | 0.9355 | 0.9778 | 9.32 ms | PASS |
| hybrid-holdout | 2026-11-02 | 512/10%/Dense+BM25/RRF k=60/k=5 | 0.8462 | 1.0000 | 0.9038 | 0.9500 | 16.93 ms | KEEP (+15.39% Hit@1, +9.35% MRR) |
| rerank-train | 2026-11-02 | 512/10%/Dense/FastReranker (50->5) | 0.9032 | 1.0000 | 0.9435 | 0.9556 | 5.12 ms | KEEP (+3.22% Hit@1) |
| rerank-holdout | 2026-11-02 | 512/10%/Dense/FastReranker (50->5) | 0.9231 | 1.0000 | 0.9615 | 0.9500 | 22.89 ms | KEEP (+23.08% Hit@1, +15.12% MRR) |
| hybrid-rerank-train | 2026-11-02 | 512/10%/Dense+BM25/RRF/FastRerank (50->5) | 0.9032 | 1.0000 | 0.9435 | 0.9556 | 6.89 ms | NEW PRODUCTION DEFAULT |
| hybrid-rerank-holdout | 2026-11-02 | 512/10%/Dense+BM25/RRF/FastRerank (50->5) | 0.9231 | 1.0000 | 0.9615 | 0.9500 | 16.29 ms | NEW PRODUCTION DEFAULT |
| hyde-holdout | 2026-11-02 | 512/10%/HyDE transform | 0.6923 | 1.0000 | 0.8103 | 0.9500 | 19.02 ms | REJECT as default (neutral, +1.5ms) |
| multi-query-holdout | 2026-11-02 | 512/10%/Multi-Query transform | 0.3846 | 1.0000 | 0.6051 | 1.0000 | 22.66 ms | REJECT as default (depresses MRR) |

## 6. Best Known Config
`chunk_size=512  overlap=51  embedder=text-embedding-3-small (mock-proj)  index=IndexFlatIP  k=5  hybrid=on (BM25+RRF k=60)  rerank=fast (top 50 -> 5)  transforms=none`
→ **Holdout Split:** Hit@1 = 0.9231, Hit@3 = 1.0000, Hit@5 = 1.0000, MRR = 0.9615, Faithfulness = 0.9500, Correctness = 0.7279, Completeness = 0.7724, Latency p95 = 16.29 ms.

## 7. Golden Set Status
Version: v1.0 · Items: 52 · Hold-out: 16 (30.8%) · Train: 36 (69.2%) · Last reviewed: 2026-11-02 (5 taxonomies: factoid, numeric, multi_sentence, no_answer, ambiguous)

## 8. Known Issues / Tech Debt & Bug Solutions
| ID | Issue | Severity | Status / Solution |
|---|---|---|---|
| BUG-001 | `pytest-asyncio` loop scope deprecation warning | Low | Fixed by adding `asyncio_default_fixture_loop_scope = "function"` to `pyproject.toml`. |
| BUG-002 | `black` scan stall on Windows scanning `.venv` | Medium | Fixed by configuring `extend-exclude = '/\.venv'` and standardizing on ultra-fast `ruff format`. |
| BUG-003 | Ruff UP042 warning on `(str, Enum)` in Python 3.11 | Low | Fixed by adopting native `enum.StrEnum` across all schema definitions. |
| BUG-004 | Header/footer regex failing on multi-dash format `--- 1 ---` | Low | Fixed regex pattern in `TextCleaner` to match `[-—–]+` instead of single dash. |
| BUG-005 | Untyped PyMuPDF call in mypy strict | Low | Typed `pdf_doc: Any` and added `# type: ignore[no-untyped-call]` on `pymupdf.open`. |
| BUG-006 | Tiktoken network download failure in sandboxed tests | High | Pre-cached encoding and added resilient word-based token approximation fallback in `SentenceTokenChunker`. |
| BUG-007 | ChromaDB MetadataValue typing union with mypy | Medium | Added safe conversion helpers `_safe_int` and `_safe_str` in `DualVectorStore`. |
| BUG-008 | Windows sandbox asyncio loopback socket hang | High | Synchronous Python generators (`Iterator[str]`) for LLM streaming and FastAPI `StreamingResponse` prevent Windows sandbox IOCP socket loop deadlocks. |
| BUG-009 | ChromaDB DuplicateIDError in search query | Medium | Deduplicated candidate IDs with `dict.fromkeys` before querying ChromaDB. |
| BUG-010 | MockLLM false positive answer matching on retrieved prompt text | Low | Scoped keyword matching strictly to extracted `QUESTION:` prompt substring. |
| BUG-011 | Windows stdout charmap UnicodeEncodeError on `\u2265` | Low | Reconfigured stdout stream to utf-8 and standardized on ASCII `>=` in report tables. |
| BUG-012 | Zero division in `partition_train_holdout` for small lists | Low | Handled single/few items with `max(1, round(len * ratio))` when ratio > 0. |
| BUG-013 | Missing module-level `import re` in `parsers.py` | Low | Added `import re` at top of `parsers.py`. |
| BUG-014 | Hit Rate denominator penalized by unanswerable questions | Medium | Filtered answerable queries for Hit Rate and MRR while evaluating abstention via Faithfulness & Correctness. |
| BUG-015 | Sentence regex split separating numbered section headers e.g. `1. Title` | Medium | Constrained `_sentence_regex` to require a letter before punctuation `(?<=[a-zA-Z][.!?])` to preserve enumerations. |
| BUG-016 | Windows OpenMP runtime DLL collision between PyMuPDF and Faiss | High | Pre-loading `faiss` in root `tests/conftest.py` ensures proper DLL handle initialization before other native extensions load. |
| BUG-017 | False grounded refusal / abstention on overview queries like "what is this about" | High | `MockLLMClient` treated generic terms ("this", "about") as keyword gates. Added overview triggers detection to generate a synthesis of top passages with proper citations and expanded stopwords so general questions never fail keyword validation. |
| BUG-018 | Missing raw file download and text preview endpoints for uploaded manuscripts | Medium | Added `get_raw_file_path` to `DocumentRegistry` and mounted `GET /v1/documents/{doc_id}/download` (FileResponse) and `GET /v1/documents/{doc_id}/preview` (extracted text & metadata). |
| BUG-019 | Infinite loop in `SentenceTokenChunker._chunk_units` causing upload freeze & "Failed to fetch" | Critical | Documents with dense code/SQL blocks without standard punctuation created sentence units exceeding chunk target size (e.g. 524 tokens). The overlap calculation retained the entire unit indefinitely without advancing the loop pointer. Resolved by splitting code/table blocks on newlines and enforcing strict monotonic shedding in overlap calculations (`len(overlap) + 1 < len(current)`). |

## 9. Lessons Learned
- Tiktoken downloads encoding files from the internet upon first invocation; in a sandboxed or offline environment, caching the file or providing an offline token estimation fallback is required.
- ChromaDB's metadata dictionary returns a broad union type (`str | int | float | SparseVector | list | None`), necessitating safe parsing helpers to guarantee strict type bounds.
- Synchronous services in FastAPI: when endpoints do CPU-bound computation (parsing, chunking, FAISS search, embedding), defining `def endpoint` allows FastAPI to use threadpool execution while eliminating asyncio loopback socket deadlock hazards on Windows.
- In RAG evaluation, unanswerable queries (where the ground truth is explicit refusal) should be excluded from the retrieval Hit Rate denominator so the metric measures true retrieval quality on answerable queries, while answer abstention is measured in faithfulness/correctness.
- Random indexing (Johnson-Lindenstrauss random projection) enables fully deterministic, high-quality term-correlated embedding representations for fast local offline testing and evaluation without requiring external embedding API calls.
- Hybrid BM25 + dense retrieval with Reciprocal Rank Fusion ($k=60$) substantially mitigates lexical blind spots in dense bi-encoders, yielding a +15.39% absolute jump in holdout Hit@1.
- Cross-encoder reranking over the top-50 candidate pool provides massive quality compounding (+23.08% Hit@1, +15.12% MRR on holdout) while adding negligible overhead (<15ms) when implemented with vectorized term-interaction features.
- Query transformation techniques such as Multi-Query and HyDE require frontier live LLMs; running them with offline/mock extractors produces noise that depresses retrieval performance. They must remain opt-in rather than enabled by default.

## 10. Changelog (newest first, 1 line each)
- 2026-11-04: Fixed infinite loop in SentenceTokenChunker during ingestion of code/SQL-heavy PDFs (e.g. `dbms_file-pratham.pdf`), eliminating long upload hang and browser "Failed to fetch" timeouts. 46 tests pass.
- 2026-11-04: Fixed false refusal abstention on general queries; built `@` mention manuscript reference dropdown, file attachment cards with preview & download, Evidentiary Manuscripts section in assistant cards, DocumentPreviewModal, and raw file download endpoint.
- 2026-11-02: Phase 6 completed. Advanced retrieval suite: Okapi BM25 sparse index, Reciprocal Rank Fusion (RRF, k=60), FastCrossEncoderReranker, ParentDocumentRetriever, QueryProcessor (HyDE, multi-query, step-back). Holdout Hit@1 improved from 0.6923 to 0.9231, MRR from 0.8103 to 0.9615. 45 tests pass.
- 2026-11-02: Phase 5 completed. React+Vite+Tailwind SPA in `frontend/` matching `design.md` design tokens ("The Reading Room"), SSE streaming chat, M-03 highlighter sweep SourceDrawer, Document Library with drag-and-drop, Evaluation Lab with metric cards and historical runs table. Production build verified (185KB JS / 17KB CSS) and mounted in FastAPI.
- 2026-11-02: Phase 4 completed. Built GoldenDatasetManager (52 items across 5 taxonomies; 70/30 split), Hit@K & MRR calculation engine, AnswerEvaluator, BenchmarkRunner, CSV/MD report generation, and CLI scripts (build_golden, run_eval, ingest). Empirical baseline verified (Hit@5=1.0, MRR=0.9355, Faith=0.9778). 34 tests pass with 100% ruff and mypy strict.
- 2026-11-02: Phase 3 completed. KNNRetriever, PromptBuilder with grounded templates and citation extraction, LiteLLM/Mock LLM clients with synchronous streaming, FastAPI endpoints (`/health`, `/documents`, `/retrieve`, `/query`, `/query/stream`), 26 tests pass with 100% ruff and mypy strict.
- 2026-11-02: Phase 2 completed. SentenceTokenChunker, MockEmbedder/LiteLLMEmbedder with L2-normalization, DualVectorStore (FAISS+Chroma), rebuild_index script, reload verified. 20 tests pass.
- 2026-11-02: Phase 1 completed. Implemented multi-format parsers (PDF/DOCX/MD/TXT), text cleaner, and SQLite document registry. 15 unit tests pass.
- 2026-11-02: Phase 0 completed. Repo scaffold, pyproject.toml, config.yaml, domain models, interfaces, logging, fixtures, and unit tests passing with full strict typing.
- 2026-11-02: memory.md initialized from template.

## 11. Update Checklist (run before ending a session)
- [x] Section 1 & 2 refreshed · [x] new decisions/experiments logged with real numbers
- [x] `phases.md` ticked · [x] ADR added if architecture changed · [x] issues updated
