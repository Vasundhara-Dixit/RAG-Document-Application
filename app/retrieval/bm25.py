"""Okapi BM25 sparse lexical indexing and search engine."""

from __future__ import annotations

import math
import re
from typing import Any

from app.models.schemas import ChunkRecord
from app.utils.logging import get_logger

logger = get_logger("bm25")

_TOKEN_RE = re.compile(r"\b\w+\b")


def tokenize_bm25(text: str) -> list[str]:
    """Tokenize text into lowercase lexical terms."""
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


class BM25Index:
    """In-memory Okapi BM25 index over ChunkRecords with metadata filtering."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize empty BM25 index."""
        self.k1 = k1
        self.b = b
        self.chunks: dict[str, ChunkRecord] = {}
        # doc_len: chunk_id -> token count
        self.doc_len: dict[str, int] = {}
        # inverted_index: term -> {chunk_id: term_frequency}
        self.inverted_index: dict[str, dict[str, int]] = {}
        # doc_freq: term -> number of chunks containing term
        self.doc_freq: dict[str, int] = {}
        self.total_tokens: int = 0
        self.avgdl: float = 0.0

    def clear(self) -> None:
        """Reset index state completely."""
        self.chunks.clear()
        self.doc_len.clear()
        self.inverted_index.clear()
        self.doc_freq.clear()
        self.total_tokens = 0
        self.avgdl = 0.0

    def count(self) -> int:
        """Total number of indexed chunks."""
        return len(self.chunks)

    def add_chunk(self, chunk: ChunkRecord) -> None:
        """Add a single chunk to the index."""
        if chunk.chunk_id in self.chunks:
            self._remove_chunk(chunk.chunk_id)

        tokens = tokenize_bm25(chunk.text)
        token_count = len(tokens)
        self.chunks[chunk.chunk_id] = chunk
        self.doc_len[chunk.chunk_id] = token_count
        self.total_tokens += token_count

        # Compute term frequencies
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        for term, freq in tf.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
                self.doc_freq[term] = 0
            self.inverted_index[term][chunk.chunk_id] = freq
            self.doc_freq[term] += 1

        self.avgdl = self.total_tokens / len(self.chunks) if self.chunks else 0.0

    def index_chunks(self, chunks: list[ChunkRecord]) -> None:
        """Batch index a list of chunks."""
        for c in chunks:
            self.add_chunk(c)
        logger.info("Indexed chunks into BM25", total_chunks=len(self.chunks), avgdl=round(self.avgdl, 2))

    def _remove_chunk(self, chunk_id: str) -> None:
        """Internal helper to remove chunk from inverted structures."""
        if chunk_id not in self.chunks:
            return

        token_count = self.doc_len.pop(chunk_id, 0)
        self.total_tokens -= token_count
        del self.chunks[chunk_id]

        # Clean inverted index
        terms_to_del: list[str] = []
        for term, postings in self.inverted_index.items():
            if chunk_id in postings:
                del postings[chunk_id]
                self.doc_freq[term] -= 1
                if self.doc_freq[term] <= 0:
                    terms_to_del.append(term)

        for term in terms_to_del:
            del self.inverted_index[term]
            del self.doc_freq[term]

        self.avgdl = self.total_tokens / len(self.chunks) if self.chunks else 0.0

    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks belonging to doc_id."""
        to_delete = [
            cid for cid, chunk in self.chunks.items() if chunk.doc_id == doc_id
        ]
        for cid in to_delete:
            self._remove_chunk(cid)
        return len(to_delete)

    def search(
        self,
        query: str,
        top_k: int = 50,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[ChunkRecord, float]]:
        """Compute Okapi BM25 relevance scores for the query."""
        if not self.chunks or not query.strip():
            return []

        query_tokens = tokenize_bm25(query)
        if not query_tokens:
            return []

        num_docs = len(self.chunks)
        scores: dict[str, float] = {}

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            # Lucene / Robertson-Spärck Jones IDF variant: ln((N - df + 0.5) / (df + 0.5) + 1)
            df = self.doc_freq[token]
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            if idf <= 0.0:
                continue

            postings = self.inverted_index[token]
            for chunk_id, tf in postings.items():
                d_len = self.doc_len.get(chunk_id, 1)
                # BM25 term saturation & document length normalization
                tf_norm = (tf * (self.k1 + 1.0)) / (
                    tf + self.k1 * (1.0 - self.b + self.b * (d_len / (self.avgdl or 1.0)))
                )
                scores[chunk_id] = scores.get(chunk_id, 0.0) + (idf * tf_norm)

        # Apply metadata filters if provided
        filtered_scores: list[tuple[ChunkRecord, float]] = []
        for chunk_id, score in scores.items():
            chunk = self.chunks[chunk_id]
            if filters:
                match = True
                for k, v in filters.items():
                    if getattr(chunk, k, None) != v:
                        match = False
                        break
                if not match:
                    continue
            filtered_scores.append((chunk, score))

        # Sort descending by score
        filtered_scores.sort(key=lambda x: x[1], reverse=True)
        return filtered_scores[:top_k]

