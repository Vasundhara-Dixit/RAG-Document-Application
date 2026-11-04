"""Unit tests for dense embedding generator and normalization."""

import numpy as np

from app.core.config import EmbeddingConfig
from app.indexing.embedder import MockEmbedder, normalize_vectors


def test_normalize_vectors() -> None:
    """Verify that normalize_vectors strictly outputs unit length vectors."""
    raw = np.array([[3.0, 4.0], [1.0, 1.0]], dtype=np.float32)
    normed = normalize_vectors(raw)

    lengths = np.linalg.norm(normed, axis=1)
    for length in lengths:
        assert np.isclose(length, 1.0, atol=1e-6)

    # First row [3, 4] normalized is [0.6, 0.8]
    assert np.isclose(normed[0, 0], 0.6)
    assert np.isclose(normed[0, 1], 0.8)


def test_mock_embedder_properties() -> None:
    """Verify MockEmbedder dimension, normalization, and determinism."""
    cfg = EmbeddingConfig(dimension=128, normalize=True)
    embedder = MockEmbedder(cfg)

    assert embedder.dimension == 128
    assert embedder.model_name == "mock-embedding-local"

    texts = [
        "First document text about cloud infrastructure.",
        "Second document text about security policies.",
    ]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 128
    assert len(vectors[1]) == 128

    # Norm should be 1.0
    arr = np.array(vectors, dtype=np.float32)
    lengths = np.linalg.norm(arr, axis=1)
    assert np.isclose(lengths[0], 1.0, atol=1e-5)
    assert np.isclose(lengths[1], 1.0, atol=1e-5)

    # Determinism: same input gives exact same embedding
    vec_repeat = embedder.embed_texts([texts[0]])[0]
    assert np.allclose(vectors[0], vec_repeat, atol=1e-6)

    # Different input gives different embedding
    assert not np.allclose(vectors[0], vectors[1], atol=1e-3)
