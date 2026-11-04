"""Dual Vector Store: In-memory FAISS search backed by ChromaDB persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
import faiss
import numpy as np
from chromadb.config import Settings as ChromaSettings

from app.core.config import IndexingConfig, get_settings
from app.core.interfaces import VectorIndex
from app.models.schemas import ChunkRecord, RetrievedPassage
from app.utils.logging import get_logger

logger = get_logger("vector_store")


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert value to integer."""
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _safe_str(val: Any, default: str = "") -> str:
    """Safely convert value to string."""
    return str(val) if val is not None else default


class DualVectorStore(VectorIndex):
    """Hybrid vector storage managing ChromaDB and FAISS IndexFlatIP search."""

    def __init__(
        self,
        dimension: int = 1536,
        config: IndexingConfig | None = None,
    ) -> None:
        """Initialize ChromaDB client and in-memory FAISS index."""
        self.config = config or get_settings().indexing
        self.dimension = dimension

        # 1. Initialize persistent ChromaDB
        self.chroma_path = Path(self.config.chroma_persist_dir)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # 2. Initialize FAISS index and ID tracking
        self.faiss_path = Path(self.config.faiss_index_path)
        self.faiss_path.parent.mkdir(parents=True, exist_ok=True)
        self.id_map_path = self.faiss_path.parent / "faiss_id_map.json"

        self.faiss_index: Any = faiss.IndexFlatIP(self.dimension)
        # Mapping from FAISS integer index row to chunk_id
        self._faiss_id_to_chunk_id: list[str] = []
        self._chunk_id_to_faiss_id: dict[str, int] = {}

        # 3. Load existing index if present, else rebuild from Chroma
        self.load()

    def get_all_chunks(self) -> list[ChunkRecord]:
        """Fetch all chunks stored in ChromaDB."""
        res = self.collection.get(include=["documents", "metadatas"])
        chunks: list[ChunkRecord] = []
        ids = res.get("ids") or []
        docs = res.get("documents") or []
        metas = res.get("metadatas") or []
        for cid, text, meta in zip(ids, docs, metas, strict=False):
            if meta is None:
                continue
            chunks.append(
                ChunkRecord(
                    chunk_id=cid,
                    doc_id=_safe_str(meta.get("doc_id")),
                    idx=_safe_int(meta.get("idx")),
                    text=_safe_str(text),
                    token_count=_safe_int(meta.get("token_count")),
                    page_start=_safe_int(meta.get("page_start", 1), 1),
                    page_end=_safe_int(meta.get("page_end", 1), 1),
                    char_start=_safe_int(meta.get("char_start")),
                    char_end=_safe_int(meta.get("char_end")),
                    section_title=_safe_str(meta.get("section_title"))
                    if meta.get("section_title")
                    else None,
                    parent_id=_safe_str(meta.get("parent_id"))
                    if meta.get("parent_id")
                    else None,
                    embedding_model=_safe_str(meta.get("embedding_model")),
                    config_hash=_safe_str(meta.get("config_hash")),
                )
            )
        return chunks

    def count(self) -> int:
        """Return total number of vectors in FAISS index."""
        return int(self.faiss_index.ntotal)

    def add(
        self,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
    ) -> None:
        """Add chunks to ChromaDB and FAISS index."""
        if not chunks:
            return

        # If any chunks already exist in index, remove previous versions first
        existing_doc_ids = {
            c.doc_id for c in chunks if c.chunk_id in self._chunk_id_to_faiss_id
        }
        if existing_doc_ids:
            for d_id in existing_doc_ids:
                self.collection.delete(where={"doc_id": d_id})
            self.rebuild_from_chroma()

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.text)
            meta: dict[str, Any] = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "idx": chunk.idx,
                "token_count": chunk.token_count,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "embedding_model": chunk.embedding_model,
                "config_hash": chunk.config_hash,
            }
            if chunk.section_title:
                meta["section_title"] = chunk.section_title
            if chunk.parent_id:
                meta["parent_id"] = chunk.parent_id
            metadatas.append(meta)

        # 1. Persist in ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,  # type: ignore[arg-type]
            documents=documents,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

        # 2. Add to FAISS index
        np_vectors = np.array(embeddings, dtype=np.float32)
        start_idx = len(self._faiss_id_to_chunk_id)
        self.faiss_index.add(np_vectors)

        for offset, cid in enumerate(ids):
            faiss_row = start_idx + offset
            self._faiss_id_to_chunk_id.append(cid)
            self._chunk_id_to_faiss_id[cid] = faiss_row

        # 3. Save FAISS index and mappings to disk
        self.save()
        logger.info(
            "Indexed chunks successfully",
            count=len(chunks),
            total_indexed=self.count(),
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedPassage]:
        """Perform nearest-neighbor search via FAISS with Chroma metadata retrieval."""
        if self.count() == 0:
            return []

        # Request more candidates if filtering is applied
        fetch_k = min(self.count(), top_k * 5 if filters else top_k)
        np_query = np.array([query_embedding], dtype=np.float32)

        scores, indices = self.faiss_index.search(np_query, fetch_k)
        matched_scores: list[float] = scores[0].tolist()
        matched_indices: list[int] = indices[0].tolist()

        candidate_ids: list[str] = []
        score_by_chunk_id: dict[str, float] = {}

        for score, idx in zip(matched_scores, matched_indices, strict=False):
            if idx < 0 or idx >= len(self._faiss_id_to_chunk_id):
                continue
            chunk_id = self._faiss_id_to_chunk_id[idx]
            candidate_ids.append(chunk_id)
            score_by_chunk_id[chunk_id] = float(score)

        if not candidate_ids:
            return []

        # Ensure IDs passed to ChromaDB are unique to avoid DuplicateIDError
        unique_candidate_ids = list(dict.fromkeys(candidate_ids))

        # Retrieve records from ChromaDB
        chroma_res = self.collection.get(
            ids=unique_candidate_ids,
            include=["documents", "metadatas"],
        )

        retrieved: list[RetrievedPassage] = []
        res_ids = chroma_res.get("ids") or []
        res_docs = chroma_res.get("documents") or []
        res_metas = chroma_res.get("metadatas") or []

        for cid, doc_text, meta in zip(res_ids, res_docs, res_metas, strict=False):
            if meta is None:
                continue

            # Apply filters if provided (e.g. {"doc_id": "..."})
            if filters:
                match = True
                for f_key, f_val in filters.items():
                    if meta.get(f_key) != f_val:
                        match = False
                        break
                if not match:
                    continue

            chunk = ChunkRecord(
                chunk_id=cid,
                doc_id=_safe_str(meta.get("doc_id")),
                idx=_safe_int(meta.get("idx")),
                text=_safe_str(doc_text),
                token_count=_safe_int(meta.get("token_count")),
                page_start=_safe_int(meta.get("page_start", 1), 1),
                page_end=_safe_int(meta.get("page_end", 1), 1),
                char_start=_safe_int(meta.get("char_start")),
                char_end=_safe_int(meta.get("char_end")),
                section_title=_safe_str(meta.get("section_title"))
                if meta.get("section_title")
                else None,
                parent_id=_safe_str(meta.get("parent_id"))
                if meta.get("parent_id")
                else None,
                embedding_model=_safe_str(meta.get("embedding_model")),
                config_hash=_safe_str(meta.get("config_hash")),
            )
            sim_score = score_by_chunk_id.get(cid, 0.0)
            retrieved.append(RetrievedPassage(chunk=chunk, score=sim_score))

        # Sort descending by score and slice to top_k
        retrieved.sort(key=lambda x: x.score, reverse=True)
        return retrieved[:top_k]

    def delete_by_doc_id(self, doc_id: str) -> int:
        """Remove all chunks for doc_id from ChromaDB and rebuild FAISS index."""
        # Find all chunks belonging to doc_id in Chroma
        res = self.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"],
        )
        target_ids = res.get("ids", [])
        if not target_ids:
            return 0

        # Delete from ChromaDB
        self.collection.delete(ids=target_ids)

        # Rebuild FAISS index from remaining ChromaDB contents
        self.rebuild_from_chroma()
        logger.info(
            "Deleted document chunks",
            doc_id=doc_id,
            deleted_count=len(target_ids),
            remaining_total=self.count(),
        )
        return len(target_ids)

    def save(self) -> None:
        """Persist FAISS index and chunk ID map to disk."""
        faiss.write_index(self.faiss_index, str(self.faiss_path))
        with open(self.id_map_path, "w", encoding="utf-8") as f:
            json.dump(self._faiss_id_to_chunk_id, f)

    def load(self) -> None:
        """Load FAISS index and ID map from disk, or rebuild from Chroma if missing."""
        if self.faiss_path.exists() and self.id_map_path.exists():
            try:
                self.faiss_index = faiss.read_index(str(self.faiss_path))
                with open(self.id_map_path, encoding="utf-8") as f:
                    self._faiss_id_to_chunk_id = json.load(f)
                self._chunk_id_to_faiss_id = {
                    cid: i for i, cid in enumerate(self._faiss_id_to_chunk_id)
                }
                logger.info(
                    "Loaded FAISS index from disk",
                    total=self.count(),
                )
                return
            except Exception as e:
                logger.warn(
                    "Failed to read FAISS index from disk, rebuilding from ChromaDB",
                    error=str(e),
                )

        # Rebuild from ChromaDB if file not found or load failed
        self.rebuild_from_chroma()

    def rebuild_from_chroma(self) -> None:
        """Reconstruct entire in-memory FAISS index from ChromaDB vectors."""
        self.faiss_index = faiss.IndexFlatIP(self.dimension)
        self._faiss_id_to_chunk_id = []
        self._chunk_id_to_faiss_id = {}

        total_in_chroma = self.collection.count()
        if total_in_chroma == 0:
            self.save()
            return

        # Fetch all records with embeddings from Chroma
        all_records = self.collection.get(
            include=["embeddings", "metadatas"],
        )
        raw_embeddings = all_records.get("embeddings")
        ids = all_records.get("ids", [])

        if raw_embeddings is not None and len(ids) > 0:
            np_vectors = np.array(raw_embeddings, dtype=np.float32)
            self.faiss_index.add(np_vectors)
            self._faiss_id_to_chunk_id = list(ids)
            self._chunk_id_to_faiss_id = {cid: idx for idx, cid in enumerate(ids)}

        self.save()
        logger.info(
            "Rebuilt FAISS index from ChromaDB",
            total_rebuilt=self.count(),
        )
