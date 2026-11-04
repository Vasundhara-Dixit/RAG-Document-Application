"""SQLite Document Registry and Upload Validation."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import IngestionConfig, get_settings
from app.models.schemas import DocumentRecord, DocumentStatus


class DocumentRegistry:
    """SQLite-backed document metadata store and validation engine."""

    def __init__(
        self,
        config: IngestionConfig | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        """Initialize registry with database connection."""
        self.config = config or get_settings().ingestion
        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            # Extract SQLite path from sqlite:///...
            raw_url = self.config.database_url
            if raw_url.startswith("sqlite:///"):
                self.db_path = Path(raw_url.replace("sqlite:///", ""))
            else:
                self.db_path = Path("data/rag_app.db")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_dir = Path(self.config.raw_data_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with sqlite row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the SQLite schema."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    mime TEXT NOT NULL,
                    pages INTEGER NOT NULL DEFAULT 1,
                    checksum TEXT NOT NULL UNIQUE,
                    uploaded_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    tags TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_checksum ON documents(checksum)"
            )
            conn.commit()

    @staticmethod
    def compute_checksum(file_bytes: bytes) -> str:
        """Compute SHA256 checksum of raw bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    def validate_upload(
        self,
        filename: str,
        file_bytes: bytes,
        mime: str = "",
    ) -> tuple[bool, str | None]:
        """Validate upload against extension, size limits, and magic bytes."""
        # 1. Size check
        if len(file_bytes) == 0:
            return False, "File is empty (0 bytes)."
        if len(file_bytes) > self.config.max_upload_size_bytes:
            max_mb = self.config.max_upload_size_bytes / (1024 * 1024)
            return False, f"File exceeds maximum allowed size of {max_mb:.1f} MB."

        # 2. Extension check
        ext = Path(filename).suffix.lower()
        if ext not in self.config.allowed_extensions:
            allowed = ", ".join(self.config.allowed_extensions)
            return False, f"File extension '{ext}' is unsupported. Allowed: {allowed}."

        # 3. Magic bytes validation
        if ext == ".pdf":
            if not file_bytes.startswith(b"%PDF-"):
                return False, "Invalid PDF file: Missing %PDF- magic header."
        elif ext == ".docx":
            # DOCX is a zip package starting with PK\x03\x04
            if not file_bytes.startswith(b"PK\x03\x04"):
                return False, "Invalid DOCX file: Missing ZIP/DOCX magic header."

        return True, None

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to avoid directory traversal and unsafe characters."""
        clean = Path(filename).name
        clean = re.sub(r"[^\w\.-]", "_", clean)
        return clean or "document"

    def get_by_checksum(self, checksum: str) -> DocumentRecord | None:
        """Lookup document by SHA256 checksum."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE checksum = ?", (checksum,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
        return None

    def get_by_doc_id(self, doc_id: str) -> DocumentRecord | None:
        """Lookup document by doc_id."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
        return None

    def get_raw_file_path(self, doc_id: str) -> Path | None:
        """Return absolute path to raw file if available."""
        doc = self.get_by_doc_id(doc_id)
        if not doc:
            return None

        # Check uploads directory first
        uploads_dir = self.raw_dir / "uploads"
        if uploads_dir.exists():
            pattern = f"{doc_id}_*"
            matches = list(uploads_dir.glob(pattern))
            if matches and matches[0].exists():
                return matches[0]

        # Check raw_dir directly
        direct_path = self.raw_dir / doc.filename
        if direct_path.exists():
            return direct_path

        # Check if any file with matching filename exists in raw_dir
        matches_raw = list(self.raw_dir.glob(f"*{doc.filename}*"))
        for m in matches_raw:
            if m.is_file() and not m.name.startswith("."):
                return m

        return None

    def register_document(
        self,
        filename: str,
        file_bytes: bytes,
        mime: str = "",
        tags: list[str] | None = None,
    ) -> tuple[DocumentRecord, bool]:
        """Validate, register, and save uploaded document.

        Returns:
            Tuple of (DocumentRecord, is_new). If already present and READY,
            returns (existing, False).
        """
        is_valid, error = self.validate_upload(filename, file_bytes, mime)
        if not is_valid:
            raise ValueError(error)

        checksum = self.compute_checksum(file_bytes)
        existing = self.get_by_checksum(checksum)
        if existing and existing.status == DocumentStatus.READY:
            return existing, False

        doc_id = checksum[:16]
        safe_name = self.sanitize_filename(filename)
        now = datetime.utcnow()

        # Save raw file in uploads subdirectory
        uploads_dir = self.raw_dir / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        file_path = uploads_dir / f"{doc_id}_{safe_name}"
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        record = DocumentRecord(
            doc_id=doc_id,
            filename=safe_name,
            mime=mime or "application/octet-stream",
            pages=1,
            checksum=checksum,
            uploaded_at=now,
            status=DocumentStatus.QUEUED,
            tags=tags or [],
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (doc_id, filename, mime, pages, checksum, uploaded_at,
                 status, error_message, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.doc_id,
                    record.filename,
                    record.mime,
                    record.pages,
                    record.checksum,
                    record.uploaded_at.isoformat(),
                    record.status.value,
                    record.error_message,
                    json.dumps(record.tags),
                ),
            )
            conn.commit()

        return record, True

    def update_status(
        self,
        doc_id: str,
        status: DocumentStatus | str,
        pages: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update processing status and page count."""
        status_val = status.value if hasattr(status, "value") else str(status)
        with self._get_connection() as conn:
            if pages is not None:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, pages = ?, error_message = ?
                    WHERE doc_id = ?
                    """,
                    (status_val, pages, error_message, doc_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, error_message = ?
                    WHERE doc_id = ?
                    """,
                    (status_val, error_message, doc_id),
                )
            conn.commit()

    def list_documents(self) -> list[DocumentRecord]:
        """List all documents ordered by upload date descending."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def delete_document(self, doc_id: str) -> bool:
        """Remove document record from registry and delete raw file."""
        record = self.get_by_doc_id(doc_id)
        if not record:
            return False

        with self._get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()

        # Delete raw file if exists
        safe_name = self.sanitize_filename(record.filename)
        file_path = self.raw_dir / f"{doc_id}_{safe_name}"
        if file_path.exists():
            file_path.unlink()

        return True

    def _row_to_record(self, row: sqlite3.Row) -> DocumentRecord:
        """Convert SQLite row to DocumentRecord."""
        raw_tags = row["tags"]
        tags: list[str] = []
        if raw_tags:
            try:
                tags = json.loads(raw_tags)
            except Exception:
                tags = []

        return DocumentRecord(
            doc_id=row["doc_id"],
            filename=row["filename"],
            mime=row["mime"],
            pages=row["pages"],
            checksum=row["checksum"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            status=DocumentStatus(row["status"]),
            error_message=row["error_message"],
            tags=tags,
        )
