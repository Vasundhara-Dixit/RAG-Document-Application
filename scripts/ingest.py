"""CLI script to ingest documents from a directory into the RAG pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.api.v1.routes import get_services
from app.models.schemas import DocumentStatus
from app.utils.logging import get_logger

logger = get_logger("ingest_cli")


def ingest_directory(dir_path: str | Path, force_reindex: bool = False) -> int:
    """Ingest all eligible document files from target directory."""
    services = get_services()
    source_dir = Path(dir_path)
    if not source_dir.exists():
        logger.error("Directory not found", path=str(source_dir))
        return 0

    eligible_extensions = {".pdf", ".docx", ".md", ".txt"}
    ingested_count = 0

    for file_path in sorted(source_dir.glob("*.*")):
        if file_path.suffix.lower() not in eligible_extensions:
            continue
        filename = file_path.name
        if filename.startswith("."):
            continue

        raw_bytes = file_path.read_bytes()
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }
        mime = mime_map.get(file_path.suffix.lower(), "text/plain")

        try:
            record, is_new = services.registry.register_document(
                filename=filename,
                file_bytes=raw_bytes,
                mime=mime,
            )
            if (
                not is_new
                and not force_reindex
                and record.status == DocumentStatus.READY
            ):
                logger.info(
                    "Document already ingested", filename=filename, doc_id=record.doc_id
                )
                continue

            services.registry.update_status(record.doc_id, DocumentStatus.PARSING)
            parsed = services.parser.parse(
                file_bytes=raw_bytes,
                filename=filename,
                mime=mime,
                checksum=record.checksum,
            )
            cleaned = services.cleaner.clean_document(parsed)

            services.registry.update_status(record.doc_id, DocumentStatus.INDEXING)
            config_hash = services.settings.get_config_hash()
            chunks = services.chunker.chunk(
                doc=cleaned,
                embedding_model=services.embedder.model_name,
                config_hash=config_hash,
            )

            if chunks:
                texts = [c.text for c in chunks]
                embeddings = services.embedder.embed_texts(texts)
                services.vector_store.add(chunks, embeddings)

            services.registry.update_status(
                doc_id=record.doc_id,
                status=DocumentStatus.READY,
                pages=cleaned.total_pages,
            )
            ingested_count += 1
            logger.info(
                "Ingested document",
                filename=filename,
                chunks=len(chunks),
                pages=cleaned.total_pages,
            )
        except Exception as e:
            logger.error("Failed to ingest document", filename=filename, error=str(e))

    return ingested_count


def main() -> None:
    """CLI entry point for document ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG vector store."
    )
    parser.add_argument(
        "--data-dir",
        default="data/raw",
        help="Directory containing raw documents to ingest",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-parsing and indexing of existing documents",
    )
    args = parser.parse_args()

    count = ingest_directory(args.data_dir, force_reindex=args.force)
    services = get_services()
    print(f"\nIngestion complete: {count} new/updated documents.")
    print(f"Total indexed chunks: {services.vector_store.count()}\n")


if __name__ == "__main__":
    main()
