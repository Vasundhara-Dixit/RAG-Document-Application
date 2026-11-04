"""Script to rebuild FAISS search index from persistent ChromaDB store."""

from app.core.config import get_settings
from app.indexing.vector_store import DualVectorStore
from app.utils.logging import get_logger, setup_logging

logger = get_logger("rebuild_script")


def main() -> None:
    """Execute index rebuild."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting FAISS rebuild from ChromaDB",
        persist_dir=settings.indexing.chroma_persist_dir,
        collection=settings.indexing.chroma_collection_name,
    )
    store = DualVectorStore(dimension=settings.embedding.dimension)
    store.rebuild_from_chroma()
    logger.info(
        "FAISS rebuild complete",
        total_vectors=store.count(),
        faiss_path=settings.indexing.faiss_index_path,
    )


if __name__ == "__main__":
    main()
