"""Unit tests for Phase 1 Ingestion, Parsers, Cleaner, and Registry."""

import io
from pathlib import Path

import pymupdf
import pytest
from docx import Document as DocxWriter

from app.ingestion.cleaner import TextCleaner
from app.ingestion.parsers import (
    DocumentParser,
    DocxParser,
    MarkdownParser,
    PDFParser,
    TextParser,
)
from app.ingestion.registry import DocumentRegistry
from app.models.schemas import DocumentStatus, ParsedDocument, ParsedPage


@pytest.fixture
def cleaner() -> TextCleaner:
    """Fixture providing text cleaner."""
    return TextCleaner()


@pytest.fixture
def parser() -> DocumentParser:
    """Fixture providing composite parser."""
    return DocumentParser()


def test_cleaner_dehyphenation(cleaner: TextCleaner) -> None:
    """Verify de-hyphenation across line breaks."""
    raw = "This is an implemen-\n  tation of the algo-\n rithm."
    cleaned = cleaner.clean_text(raw)
    assert "implementation" in cleaned
    assert "algorithm" in cleaned
    assert "implemen-" not in cleaned


def test_cleaner_headers_footers(cleaner: TextCleaner) -> None:
    """Verify stripping of page number headers and footers."""
    raw = "Header content.\nPage 1 of 5\nBody paragraph text.\n--- 1 ---\nFooter note."
    cleaned = cleaner.clean_text(raw)
    assert "Page 1 of 5" not in cleaned
    assert "--- 1 ---" not in cleaned
    assert "Body paragraph text." in cleaned


def test_cleaner_whitespace_and_unicode(cleaner: TextCleaner) -> None:
    """Verify unicode normalization and whitespace collapsing."""
    raw = (
        "Here   is   text   with   multiple    spaces.\n\n\n\n"
        "New paragraph with “curly quotes”."
    )
    cleaned = cleaner.clean_text(raw)
    assert "Here is text with multiple spaces." in cleaned
    assert "\n\n\n" not in cleaned
    assert '"curly quotes"' in cleaned or "“curly quotes”" in unicodedata_norm(cleaned)


def unicodedata_norm(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKC", s)


def test_cleaner_clean_document(cleaner: TextCleaner) -> None:
    """Verify clean_document preserves page structure and updates offsets."""
    pages = [
        ParsedPage(
            page_number=1,
            text="Page   one   text.",
            char_offset_start=0,
            char_offset_end=20,
        ),
        ParsedPage(
            page_number=2,
            text="Page   two   text.",
            char_offset_start=21,
            char_offset_end=41,
        ),
    ]
    doc = ParsedDocument(
        doc_id="doc1",
        filename="test.txt",
        mime="text/plain",
        checksum="123456",
        pages=pages,
        total_pages=2,
    )
    cleaned_doc = cleaner.clean_document(doc)
    assert cleaned_doc.total_pages == 2
    assert cleaned_doc.pages[0].text == "Page one text."
    assert cleaned_doc.pages[1].text == "Page two text."
    assert cleaned_doc.pages[0].char_offset_end == len("Page one text.")


def test_pdf_parser_with_generated_pdf() -> None:
    """Verify PDF extraction across multiple pages using PyMuPDF."""
    doc = pymupdf.open()
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 72), "First page heading\nThis is paragraph one on page 1.")
    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Second page heading\nThis is paragraph two on page 2.")

    pdf_bytes = doc.tobytes()
    doc.close()

    parser = PDFParser()
    assert parser.can_parse("sample.pdf", "application/pdf")

    parsed = parser.parse(pdf_bytes, "sample.pdf", "application/pdf", "dummy_checksum")
    assert parsed.total_pages == 2
    assert parsed.pages[0].page_number == 1
    assert "First page heading" in parsed.pages[0].text
    assert parsed.pages[1].page_number == 2
    assert "Second page heading" in parsed.pages[1].text


def test_docx_parser_with_generated_docx() -> None:
    """Verify DOCX extraction including paragraphs and tables."""
    docx_file = DocxWriter()
    docx_file.add_heading("Architecture Overview", level=1)
    docx_file.add_paragraph("This is the main text of the DOCX document.")

    table = docx_file.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Component"
    table.rows[0].cells[1].text = "Role"
    table.rows[1].cells[0].text = "FAISS"
    table.rows[1].cells[1].text = "Search"

    buf = io.BytesIO()
    docx_file.save(buf)
    docx_bytes = buf.getvalue()

    parser = DocxParser()
    assert parser.can_parse(
        "report.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    parsed = parser.parse(docx_bytes, "report.docx", "", "docx_checksum")
    assert parsed.total_pages >= 1
    combined_text = "\n".join(p.text for p in parsed.pages)
    assert "Architecture Overview" in combined_text
    assert "This is the main text of the DOCX document." in combined_text
    assert "Component | Role" in combined_text
    assert "FAISS | Search" in combined_text


def test_markdown_parser() -> None:
    """Verify Markdown parsing and explicit page break detection."""
    md_content = """# Section 1
This is text on page 1.
<!-- pagebreak -->
# Section 2
This is text on page 2.
"""
    parser = MarkdownParser()
    assert parser.can_parse("doc.md", "text/markdown")

    parsed = parser.parse(
        md_content.encode("utf-8"), "doc.md", "text/markdown", "md_checksum"
    )
    assert parsed.total_pages == 2
    assert "Section 1" in parsed.pages[0].text
    assert "Section 2" in parsed.pages[1].text


def test_text_parser() -> None:
    """Verify plain text parser with form-feed page separator."""
    txt_content = "Page 1 content.\x0cPage 2 content."
    parser = TextParser()
    assert parser.can_parse("file.txt", "text/plain")

    parsed = parser.parse(
        txt_content.encode("utf-8"), "file.txt", "text/plain", "txt_checksum"
    )
    assert parsed.total_pages == 2
    assert "Page 1 content." in parsed.pages[0].text
    assert "Page 2 content." in parsed.pages[1].text


def test_document_parser_dispatcher(parser: DocumentParser) -> None:
    """Verify dispatcher automatically picks the right format parser."""
    parsed_txt = parser.parse(b"Hello text", "note.txt", "text/plain", "c1")
    assert parsed_txt.total_pages == 1

    parsed_md = parser.parse(b"# Hello MD", "note.md", "text/markdown", "c2")
    assert parsed_md.total_pages == 1

    with pytest.raises(ValueError, match="Unsupported file format"):
        parser.parse(b"data", "image.png", "image/png", "c3")


def test_registry_validation_and_idempotency(tmp_path: Path) -> None:
    """Verify upload validation, magic byte checks, and idempotent registration."""
    db_file = tmp_path / "test_rag.db"
    registry = DocumentRegistry(db_path=db_file)

    # 1. Reject empty file
    with pytest.raises(ValueError, match="File is empty"):
        registry.register_document("empty.txt", b"", "text/plain")

    # 2. Reject unsupported extension
    with pytest.raises(ValueError, match="unsupported"):
        registry.register_document("script.sh", b"echo hello", "text/x-sh")

    # 3. Reject invalid PDF magic bytes
    with pytest.raises(ValueError, match="Missing %PDF-"):
        registry.register_document("fake.pdf", b"Not a real PDF", "application/pdf")

    # 4. Reject invalid DOCX magic bytes
    with pytest.raises(ValueError, match="Missing ZIP/DOCX"):
        registry.register_document("fake.docx", b"Not a real docx", "application/docx")

    # 5. Successful registration of valid text
    valid_bytes = b"Corporate security policy guidelines."
    record1, is_new1 = registry.register_document(
        "policy.txt", valid_bytes, "text/plain"
    )
    assert is_new1 is True
    assert record1.filename == "policy.txt"
    assert record1.status == DocumentStatus.QUEUED

    # Update to READY
    registry.update_status(record1.doc_id, DocumentStatus.READY, pages=1)

    # 6. Idempotency check: same file uploaded again
    record2, is_new2 = registry.register_document(
        "policy.txt", valid_bytes, "text/plain"
    )
    assert is_new2 is False
    assert record2.doc_id == record1.doc_id
    assert record2.status == DocumentStatus.READY

    # 7. List documents
    docs = registry.list_documents()
    assert len(docs) == 1
    assert docs[0].doc_id == record1.doc_id

    # 8. Delete document
    deleted = registry.delete_document(record1.doc_id)
    assert deleted is True
    assert len(registry.list_documents()) == 0
