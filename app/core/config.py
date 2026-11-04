"""Configuration management with Pydantic validation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application level settings."""

    name: str = "RAG Document Q&A"
    version: str = "0.1.0"
    env: str = "development"
    allow_external_llm: bool = False


class IngestionConfig(BaseModel):
    """Document upload and storage settings."""

    max_upload_size_bytes: int = 26214400  # 25 MB
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".md", ".txt"]
    )
    raw_data_dir: str = "data/raw"
    database_url: str = "sqlite:///data/rag_app.db"


class CleanerConfig(BaseModel):
    """Text normalization and cleaning rules."""

    strip_headers_footers: bool = True
    normalize_unicode: bool = True
    collapse_whitespace: bool = True
    dehyphenate: bool = True


class ChunkingConfig(BaseModel):
    """Sentence-boundary and token chunking parameters."""

    chunk_size: int = 512
    chunk_overlap: int = 51
    tokenizer_model: str = "cl100k_base"
    contextual_enrichment: bool = False
    child_chunk_size: int = 128


class EmbeddingConfig(BaseModel):
    """Embedding model parameters."""

    model_name: str = "text-embedding-3-small"
    dimension: int = 1536
    normalize: bool = True
    batch_size: int = 32


class IndexingConfig(BaseModel):
    """Vector index and persistence parameters."""

    chroma_persist_dir: str = "data/index/chroma"
    chroma_collection_name: str = "rag_chunks"
    faiss_index_path: str = "data/index/faiss.index"
    index_type: str = "IndexFlatIP"


class RetrievalConfig(BaseModel):
    """Retriever execution parameters."""

    default_k: int = 5
    score_threshold: float = -1.0
    hybrid_enabled: bool = True
    rrf_k: int = 60
    dense_weight: float = 1.0
    bm25_weight: float = 1.0
    reranker_enabled: bool = True
    reranker_type: str = "fast"
    reranker_top_k: int = 5
    reranker_candidates: int = 50
    query_transform_strategy: str = "none"
    parent_retrieval_enabled: bool = False


class GenerationConfig(BaseModel):
    """LLM generation and prompting parameters."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_seconds: int = 30
    max_retries: int = 3
    abstain_message: str = (
        "The documents don't contain enough information to answer this."
    )
    system_prompt: str = ""


class EvalConfig(BaseModel):
    """Evaluation harness thresholds and parameters."""

    judge_model: str = "gpt-4o"
    judge_temperature: float = 0.0
    golden_set_dir: str = "data/golden"
    holdout_ratio: float = 0.30
    target_hit_rate_at_5: float = 0.85
    target_mrr: float = 0.65
    target_faithfulness: float = 0.90


class Settings(BaseModel):
    """Root configuration model."""

    app: AppConfig = Field(default_factory=AppConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    cleaner: CleanerConfig = Field(default_factory=CleanerConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)

    def get_config_hash(self) -> str:
        """Compute SHA256 hash of chunking and embedding settings."""
        hash_payload = {
            "chunking": self.chunking.model_dump(),
            "embedding": self.embedding.model_dump(),
        }
        canonical_json = json.dumps(hash_payload, sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:16]


_GLOBAL_SETTINGS: Settings | None = None


def load_config(config_path: str | Path | None = None) -> Settings:
    """Load configuration from YAML file with environment variable fallbacks."""
    global _GLOBAL_SETTINGS

    resolved_path: Path
    if config_path is not None:
        resolved_path = Path(config_path)
    else:
        env_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
        resolved_path = Path(env_path)

    data: dict[str, Any] = {}
    if resolved_path.is_file():
        with open(resolved_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                data = loaded

    settings = Settings.model_validate(data)

    # Check environment variable overrides
    if os.getenv("ALLOW_EXTERNAL_LLM") is not None:
        settings.app.allow_external_llm = (
            os.getenv("ALLOW_EXTERNAL_LLM", "false").lower() == "true"
        )

    _GLOBAL_SETTINGS = settings
    return settings


def get_settings() -> Settings:
    """Retrieve global cached settings or load default."""
    global _GLOBAL_SETTINGS
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = load_config()
    return _GLOBAL_SETTINGS
