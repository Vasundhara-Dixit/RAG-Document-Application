"""Document parsers for PDF, DOCX, Markdown, and TXT files."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pymupdf
from docx import Document as DocxReader

from app.core.interfaces import Parser
from app.models.schemas import ParsedDocument, ParsedPage


class PDFParser(Parser):
    """Parser for PDF documents using PyMuPDF."""

    def can_parse(self, filename: str, mime: str) -> bool:
        """Check if file is a PDF."""
        return (
            filename.lower().endswith(".pdf")
            or mime == "application/pdf"
            or mime == "application/x-pdf"
        )

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str,
        checksum: str,
    ) -> ParsedDocument:
        """Extract text and page numbers from PDF bytes."""
        try:
            pdf_doc: Any = pymupdf.open(  # type: ignore[no-untyped-call]
                stream=file_bytes, filetype="pdf"
            )
        except Exception as e:
            raise ValueError(f"Failed to open PDF document: {e}") from e

        if pdf_doc.is_encrypted:
            pdf_doc.close()
            raise ValueError("Encrypted/password-protected PDFs are not supported.")

        pages: list[ParsedPage] = []
        current_offset = 0

        for page_idx in range(len(pdf_doc)):
            page = pdf_doc[page_idx]
            page_text = str(page.get_text("text") or "")
            char_len = len(page_text)
            pages.append(
                ParsedPage(
                    page_number=page_idx + 1,
                    text=page_text,
                    char_offset_start=current_offset,
                    char_offset_end=current_offset + char_len,
                )
            )
            current_offset += char_len + 1

        total_pages = len(pages)
        raw_meta = pdf_doc.metadata or {}
        metadata: dict[str, Any] = {
            "title": raw_meta.get("title", ""),
            "author": raw_meta.get("author", ""),
            "subject": raw_meta.get("subject", ""),
            "total_pages": total_pages,
        }
        pdf_doc.close()

        doc_id = checksum[:16]
        return ParsedDocument(
            doc_id=doc_id,
            filename=filename,
            mime=mime or "application/pdf",
            checksum=checksum,
            pages=pages,
            total_pages=total_pages,
            metadata=metadata,
        )


class DocxParser(Parser):
    """Parser for Microsoft Word (.docx) files."""

    def can_parse(self, filename: str, mime: str) -> bool:
        """Check if file is a DOCX."""
        return (
            filename.lower().endswith(".docx")
            or mime
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str,
        checksum: str,
    ) -> ParsedDocument:
        """Extract paragraphs and tables from DOCX bytes."""
        try:
            docx = DocxReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX file: {e}") from e

        paragraphs_text: list[str] = []
        for p in docx.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs_text.append(text)

        # Extract table contents cleanly
        for table in docx.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    paragraphs_text.append(row_text)

        # Segment into virtual pages (~400 words per page if no native page markers)
        full_text = "\n\n".join(paragraphs_text)
        words = full_text.split()
        words_per_page = 400

        pages: list[ParsedPage] = []
        current_offset = 0

        if not words:
            pages.append(
                ParsedPage(
                    page_number=1,
                    text="",
                    char_offset_start=0,
                    char_offset_end=0,
                )
            )
        else:
            page_num = 1
            for i in range(0, len(words), words_per_page):
                page_words = words[i : i + words_per_page]
                page_text = " ".join(page_words)
                char_len = len(page_text)
                pages.append(
                    ParsedPage(
                        page_number=page_num,
                        text=page_text,
                        char_offset_start=current_offset,
                        char_offset_end=current_offset + char_len,
                    )
                )
                current_offset += char_len + 1
                page_num += 1

        doc_id = checksum[:16]
        docx_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return ParsedDocument(
            doc_id=doc_id,
            filename=filename,
            mime=mime or docx_mime,
            checksum=checksum,
            pages=pages,
            total_pages=len(pages),
            metadata={"paragraph_count": len(paragraphs_text)},
        )


class MarkdownParser(Parser):
    """Parser for Markdown (.md) documents."""

    def can_parse(self, filename: str, mime: str) -> bool:
        """Check if file is Markdown."""
        return (
            filename.lower().endswith((".md", ".markdown"))
            or mime == "text/markdown"
            or mime == "text/x-markdown"
        )

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str,
        checksum: str,
    ) -> ParsedDocument:
        """Extract markdown text, handling explicit page breaks or headers."""
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1", errors="replace")

        # Check for explicit page separators or numbered section headers
        raw_pages: list[str] = []
        if "<!-- pagebreak -->" in content:
            raw_pages = content.split("<!-- pagebreak -->")
        elif "\x0c" in content:
            raw_pages = content.split("\x0c")
        elif re.search(r"(?:^|\n)## \d+\.", content):
            splits = re.split(r"(?=(?:^|\n)## \d+\.)", content)
            raw_pages = [s for s in splits if s.strip()]
        else:
            # Paginate by 400 words
            words = content.split()
            words_per_page = 400
            if not words:
                raw_pages = [""]
            else:
                for i in range(0, len(words), words_per_page):
                    raw_pages.append(" ".join(words[i : i + words_per_page]))

        pages: list[ParsedPage] = []
        current_offset = 0
        for idx, page_str in enumerate(raw_pages, start=1):
            cleaned_p = page_str.strip()
            char_len = len(cleaned_p)
            pages.append(
                ParsedPage(
                    page_number=idx,
                    text=cleaned_p,
                    char_offset_start=current_offset,
                    char_offset_end=current_offset + char_len,
                )
            )
            current_offset += char_len + 1

        doc_id = checksum[:16]
        return ParsedDocument(
            doc_id=doc_id,
            filename=filename,
            mime=mime or "text/markdown",
            checksum=checksum,
            pages=pages,
            total_pages=len(pages),
            metadata={"format": "markdown"},
        )


class TextParser(Parser):
    """Parser for plain text (.txt) documents."""

    def can_parse(self, filename: str, mime: str) -> bool:
        """Check if file is plain text."""
        return filename.lower().endswith(".txt") or mime == "text/plain"

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str,
        checksum: str,
    ) -> ParsedDocument:
        """Extract plain text, paginating by form-feed or word count."""
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1", errors="replace")

        # Split on form feed or Page marker if present, else paginate by 400 words
        raw_pages: list[str] = []
        if "\x0c" in content:
            raw_pages = content.split("\x0c")
        elif re.search(r"(?:^|\n)Page \d+", content):
            splits = re.split(r"(?:^|\n)Page \d+", content)
            raw_pages = [s for s in splits if s.strip()]
        else:
            words = content.split()
            words_per_page = 400
            if not words:
                raw_pages = [""]
            else:
                for i in range(0, len(words), words_per_page):
                    raw_pages.append(" ".join(words[i : i + words_per_page]))

        pages: list[ParsedPage] = []
        current_offset = 0
        for idx, page_str in enumerate(raw_pages, start=1):
            cleaned_p = page_str.strip()
            char_len = len(cleaned_p)
            pages.append(
                ParsedPage(
                    page_number=idx,
                    text=cleaned_p,
                    char_offset_start=current_offset,
                    char_offset_end=current_offset + char_len,
                )
            )
            current_offset += char_len + 1

        doc_id = checksum[:16]
        return ParsedDocument(
            doc_id=doc_id,
            filename=filename,
            mime=mime or "text/plain",
            checksum=checksum,
            pages=pages,
            total_pages=len(pages),
            metadata={"format": "plain_text"},
        )


class DocumentParser:
    """Composite document parser that routes to the appropriate format parser."""

    def __init__(self) -> None:
        """Register all supported parsers."""
        self.parsers: list[Parser] = [
            PDFParser(),
            DocxParser(),
            MarkdownParser(),
            TextParser(),
        ]

    def get_parser(self, filename: str, mime: str = "") -> Parser:
        """Find the matching parser for a filename or MIME type."""
        for parser in self.parsers:
            if parser.can_parse(filename, mime):
                return parser
        ext = Path(filename).suffix
        msg = (
            f"Unsupported file format '{ext}'."
            " Supported formats: .pdf, .docx, .md, .txt"
        )
        raise ValueError(msg)

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime: str = "",
        checksum: str = "",
    ) -> ParsedDocument:
        """Parse file bytes using the appropriate parser."""
        parser = self.get_parser(filename, mime)
        return parser.parse(file_bytes, filename, mime, checksum)
