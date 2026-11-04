"""Text cleaning and normalization pipeline stage."""

from __future__ import annotations

import re
import unicodedata

from app.core.config import CleanerConfig, get_settings
from app.core.interfaces import Cleaner
from app.models.schemas import ParsedDocument, ParsedPage


class TextCleaner(Cleaner):
    """Production-grade text cleaner for parsed document text."""

    def __init__(self, config: CleanerConfig | None = None) -> None:
        """Initialize cleaner with configuration."""
        self.config = config or get_settings().cleaner
        # Regex patterns for cleaning
        self._hyphen_regex = re.compile(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)")
        self._header_footer_regex = re.compile(
            r"^(?:(?:page\s+\d+(?:\s+of\s+\d+)?)|(?:\d+\s+/\s+\d+)|(?:[-—–]+\s*\d+\s*[-—–]+))\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        self._multiple_newlines_regex = re.compile(r"\n{3,}")
        self._multiple_spaces_regex = re.compile(r"[^\S\r\n]{2,}")
        self._control_chars_regex = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def clean_text(self, text: str) -> str:
        """Clean a single string following configuration rules."""
        if not text:
            return ""

        cleaned = text

        # 1. Unicode normalization (NFKC ensures standard quotes, dashes, accents)
        if self.config.normalize_unicode:
            cleaned = unicodedata.normalize("NFKC", cleaned)

        # 2. Remove non-printable control characters (except tab and newline)
        cleaned = self._control_chars_regex.sub("", cleaned)

        # 3. Strip page number headers/footers
        if self.config.strip_headers_footers:
            cleaned = self._header_footer_regex.sub("", cleaned)

        # 4. De-hyphenate words broken across line breaks
        if self.config.dehyphenate:
            cleaned = self._hyphen_regex.sub(r"\1\2", cleaned)

        # 5. Collapse excessive whitespace
        if self.config.collapse_whitespace:
            # Replace 2+ horizontal spaces with a single space
            cleaned = self._multiple_spaces_regex.sub(" ", cleaned)
            # Replace 3+ consecutive newlines with two newlines
            cleaned = self._multiple_newlines_regex.sub("\n\n", cleaned)
            # Trim surrounding whitespace per line
            lines = [line.strip() for line in cleaned.split("\n")]
            cleaned = "\n".join(lines).strip()

        return cleaned

    def clean_document(self, doc: ParsedDocument) -> ParsedDocument:
        """Apply cleaning across all pages in a parsed document."""
        cleaned_pages: list[ParsedPage] = []
        current_offset = 0

        for page in doc.pages:
            cleaned_page_text = self.clean_text(page.text)
            char_length = len(cleaned_page_text)
            cleaned_pages.append(
                ParsedPage(
                    page_number=page.page_number,
                    text=cleaned_page_text,
                    char_offset_start=current_offset,
                    char_offset_end=current_offset + char_length,
                )
            )
            current_offset += char_length + 1  # 1 for newline separator

        return ParsedDocument(
            doc_id=doc.doc_id,
            filename=doc.filename,
            mime=doc.mime,
            checksum=doc.checksum,
            pages=cleaned_pages,
            total_pages=len(cleaned_pages),
            metadata=doc.metadata,
        )
