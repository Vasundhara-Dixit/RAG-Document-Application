# ADR-002: Pluggable Interfaces for Pipeline Stages

## Status
Accepted

## Context
The RAG pipeline evolves through 8 delivery phases: Tier 1 MVP (dense FAISS + Chroma), Tier 2 (BM25 + Cross-Encoder reranking + query expansion), Tier 3 (OCR/table extraction), through Tier 5 (semantic caching and enterprise hardening).
Coupling pipeline stages to specific vendor SDKs or implementations would lead to brittle code and difficult refactoring.

## Decision
All pipeline stages must implement abstract base classes defined in `app/core/interfaces.py`:
- `Parser`
- `Cleaner`
- `Chunker`
- `Embedder`
- `VectorIndex`
- `Retriever`
- `Reranker`
- `LLM`

Dependency injection via FastAPI and class constructors will be used across the application.

## Consequences
- Every new algorithm (e.g., Cross-Encoder reranking or BM25 retrieval) can be swapped in or compared against baseline in the evaluation harness without altering surrounding orchestration.
- 100% type safety and strict mypy compliance across all modules.

