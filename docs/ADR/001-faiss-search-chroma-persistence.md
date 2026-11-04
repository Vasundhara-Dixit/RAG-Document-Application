# ADR-001: FAISS for Search + ChromaDB for Persistence

## Status
Accepted

## Context
A production RAG application requires both ultra-fast nearest-neighbor similarity search (p95 retrieval < 300 ms) and durable, queryable persistence of chunk text, provenance, and metadata (page numbers, character offsets, document checksums, config hashes).
Relying solely on ChromaDB for in-memory ANN search can introduce latency overhead under high concurrency, while using FAISS alone lacks native ACID metadata filtering, relational joins, and persistent document tracking without building custom disk serialisation formats.

## Decision
We decouple search and persistence:
1. **ChromaDB:** Durable document chunk store, vector archive, and metadata filter registry.
2. **FAISS (`IndexFlatIP`):** High-speed vector index loaded into memory, performing inner product search (equivalent to cosine similarity on L2-normalized vectors).
3. **Join Key:** `chunk_id` is the deterministic join key between FAISS integer IDs and Chroma chunk records.
4. **Rebuildability:** The FAISS index is completely rebuildable from ChromaDB and raw files at any time.

## Consequences
- Requires maintaining dual indices during document addition and deletion.
- Ensures < 50ms vector query times via FAISS while preserving rich metadata filtering and persistence via ChromaDB.

