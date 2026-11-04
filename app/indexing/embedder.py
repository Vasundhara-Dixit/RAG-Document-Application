"""Dense embedding generation with L2-normalization."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import numpy.typing as npt

from app.core.config import EmbeddingConfig, get_settings
from app.core.interfaces import Embedder
from app.utils.logging import get_logger

logger = get_logger("embedder")


def normalize_vectors(
    vectors: npt.NDArray[np.float32],
) -> npt.NDArray[np.float32]:
    """L2-normalize rows of a 2D float32 array so that norm == 1.0."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero
    norms = np.where(norms == 0, 1.0, norms)
    normalized: npt.NDArray[np.float32] = (vectors / norms).astype(np.float32)
    return normalized


class MockEmbedder(Embedder):
    """Deterministic local embedder for testing and offline execution."""

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        """Initialize mock embedder with target dimension."""
        self.config = config or get_settings().embedding
        self._dim = self.config.dimension
        self._model_name = "mock-embedding-local"

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return vector dimension."""
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic normalized float32 vectors based on text hash."""
        if not texts:
            return []

        raw_vectors: list[list[float]] = []
        for text in texts:
            import re

            words = re.findall(r"\b[a-zA-Z0-9_\$]+\b", text.lower())
            if not words:
                vec = np.zeros(self._dim, dtype=np.float32)
                vec[0] = 1.0
            else:
                vec = np.zeros(self._dim, dtype=np.float32)
                for w in words:
                    w_hash = hashlib.sha256(w.encode("utf-8")).digest()
                    seed = int.from_bytes(w_hash[:4], "big")
                    rng = np.random.RandomState(seed)
                    token_vec = rng.randn(self._dim).astype(np.float32)
                    vec += token_vec

            raw_vectors.append(vec.tolist())

        arr = np.array(raw_vectors, dtype=np.float32)
        if self.config.normalize:
            arr = normalize_vectors(arr)

        return arr.tolist()  # type: ignore[no-any-return]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query."""
        results = self.embed_texts([query])
        return results[0]


class LiteLLMEmbedder(Embedder):
    """Embedder using LiteLLM to interface with LLM embedding APIs."""

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        """Initialize LiteLLM embedder."""
        self.config = config or get_settings().embedding
        self._model_name = self.config.model_name
        self._dim = self.config.dimension

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return vector dimension."""
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts with batching and L2-normalization."""
        if not texts:
            return []

        import litellm

        all_vectors: list[list[float]] = []
        batch_size = max(1, self.config.batch_size)

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response: Any = litellm.embedding(
                    model=self._model_name,
                    input=batch,
                )
                batch_vectors = [item["embedding"] for item in response.data]
                all_vectors.extend(batch_vectors)
            except Exception as e:
                logger.error(
                    "LiteLLM embedding call failed",
                    model=self._model_name,
                    error=str(e),
                )
                raise RuntimeError(
                    f"Embedding generation failed for model {self._model_name}: {e}"
                ) from e

        arr = np.array(all_vectors, dtype=np.float32)
        if self.config.normalize:
            arr = normalize_vectors(arr)

        return arr.tolist()  # type: ignore[no-any-return]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        results = self.embed_texts([query])
        return results[0]


def get_embedder(
    config: EmbeddingConfig | None = None,
    force_mock: bool = False,
) -> Embedder:
    """Return configured embedder; falls back to MockEmbedder if offline."""
    settings = get_settings()
    emb_config = config or settings.embedding

    if force_mock or not settings.app.allow_external_llm:
        return MockEmbedder(emb_config)
    return LiteLLMEmbedder(emb_config)
