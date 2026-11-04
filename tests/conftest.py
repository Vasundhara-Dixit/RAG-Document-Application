"""Pytest configuration and root test fixtures."""

from __future__ import annotations

# Pre-load pymupdf and faiss before other C extensions to prevent Windows OpenMP DLL conflict
try:
    import pymupdf  # noqa: F401 # isort: skip
    import faiss  # noqa: F401
except ImportError:
    pass

