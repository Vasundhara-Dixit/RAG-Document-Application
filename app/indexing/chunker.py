"""Sentence-aware, token-bounded document chunker supporting contextual enrichment and hierarchy."""

from __future__ import annotations

import re
from typing import Any, TypedDict

import tiktoken

from app.core.config import ChunkingConfig, get_settings
from app.core.interfaces import Chunker
from app.models.schemas import ChunkRecord, ParsedDocument


class SentenceUnit(TypedDict):
    """Metadata for an atomic sentence unit."""

    text: str
    tokens: int
    page: int
    char_start: int
    char_end: int
    section_title: str | None


class SentenceTokenChunker(Chunker):
    """Chunks documents preserving sentence boundaries within token budget."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        """Initialize chunker with token encoder and config."""
        self.config = config or get_settings().chunking
        try:
            self.encoder: Any = tiktoken.get_encoding(self.config.tokenizer_model)
        except Exception:
            self.encoder = None

        # Sentence split regex: split on sentence terminators preceded by a letter, followed by capital
        self._sentence_regex = re.compile(r"(?<=[a-zA-Z][.!?])\s+(?=[A-Z0-9\"'(\[])")
        # Section header detector (Markdown # or numbered e.g. 1.2 or all-caps)
        self._header_regex = re.compile(
            r"^(?:#{1,6}\s+|(?:\d+\.)+\s+|[A-Z0-9\s]{4,}:)(.*)",
            re.MULTILINE,
        )

    def count_tokens(self, text: str) -> int:
        """Return token count with resilient offline fallback."""
        if self.encoder is not None:
            try:
                return len(self.encoder.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Fallback approximation: ~1.3 tokens per whitespace word
        return max(1, int(len(text.split()) * 1.3))

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences, falling back to paragraphs, newlines, or clauses."""
        paragraphs = text.split("\n\n")
        sentences: list[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            parts = self._sentence_regex.split(para)
            for part in parts:
                clean_part = part.strip()
                if not clean_part:
                    continue
                # If part has internal newlines and exceeds 120 tokens (e.g. code/tables), break on newlines
                if "\n" in clean_part and self.count_tokens(clean_part) > 120:
                    lines = [ln.strip() for ln in clean_part.splitlines() if ln.strip()]
                    sentences.extend(lines)
                else:
                    sentences.append(clean_part)
        return sentences

    def _extract_section_title(self, text: str) -> str | None:
        """Detect section title if present in sentence or paragraph."""
        for line in text.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            if clean_line.startswith("#"):
                clean = re.sub(r"^#{1,6}\s*", "", clean_line).strip()
                if clean:
                    return clean[:60]
            if re.match(r"^\d+(\.\d+)*\.?\s+[A-Z]", clean_line):
                return clean_line[:60]
        return None

    def chunk(
        self,
        doc: ParsedDocument,
        embedding_model: str,
        config_hash: str,
    ) -> list[ChunkRecord]:
        """Split parsed document into token-bounded chunks with provenance."""
        sentence_units = self._extract_sentence_units(doc)
        if not sentence_units:
            return []

        return self._chunk_units(
            sentence_units=sentence_units,
            doc=doc,
            target_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap,
            embedding_model=embedding_model,
            config_hash=config_hash,
            prefix_id="",
            parent_id=None,
        )

    def chunk_hierarchical(
        self,
        doc: ParsedDocument,
        embedding_model: str,
        config_hash: str,
        parent_size: int | None = None,
        child_size: int | None = None,
    ) -> tuple[list[ChunkRecord], list[ChunkRecord]]:
        """Split parsed document into parent chunks and smaller child chunks linked via parent_id."""
        sentence_units = self._extract_sentence_units(doc)
        if not sentence_units:
            return [], []

        p_size = parent_size or self.config.chunk_size
        c_size = child_size or self.config.child_chunk_size
        p_overlap = self.config.chunk_overlap
        c_overlap = max(10, int(c_size * 0.15))

        # 1. Build parent chunks
        parents = self._chunk_units(
            sentence_units=sentence_units,
            doc=doc,
            target_size=p_size,
            overlap=p_overlap,
            embedding_model=embedding_model,
            config_hash=config_hash,
            prefix_id="p_",
            parent_id=None,
        )

        # 2. Build child chunks within each parent
        children: list[ChunkRecord] = []
        child_idx = 0
        for parent in parents:
            # Sub-split parent text into smaller units
            p_sents = self._split_into_sentences(parent.text)
            p_units: list[SentenceUnit] = [
                {
                    "text": s,
                    "tokens": self.count_tokens(s),
                    "page": parent.page_start,
                    "char_start": parent.char_start,
                    "char_end": parent.char_end,
                    "section_title": parent.section_title,
                }
                for s in p_sents
            ]
            p_children = self._chunk_units(
                sentence_units=p_units,
                doc=doc,
                target_size=c_size,
                overlap=c_overlap,
                embedding_model=embedding_model,
                config_hash=config_hash,
                prefix_id="c_",
                parent_id=parent.chunk_id,
                start_idx=child_idx,
            )
            children.extend(p_children)
            child_idx += len(p_children)

        return parents, children

    def _extract_sentence_units(self, doc: ParsedDocument) -> list[SentenceUnit]:
        """Extract atomic sentence units across all pages."""
        sentence_units: list[SentenceUnit] = []
        current_section: str | None = None

        for page in doc.pages:
            page_text = page.text
            if not page_text.strip():
                continue
            sents = self._split_into_sentences(page_text)
            page_offset = page.char_offset_start

            for s in sents:
                detected_section = self._extract_section_title(s)
                if detected_section:
                    current_section = detected_section

                start_in_page = page_text.find(s)
                if start_in_page == -1:
                    start_in_page = 0
                c_start = page_offset + start_in_page
                c_end = c_start + len(s)
                s_tokens = self.count_tokens(s)
                sentence_units.append(
                    {
                        "text": s,
                        "tokens": s_tokens,
                        "page": page.page_number,
                        "char_start": c_start,
                        "char_end": c_end,
                        "section_title": current_section,
                    }
                )
        return sentence_units

    def _chunk_units(
        self,
        sentence_units: list[SentenceUnit],
        doc: ParsedDocument,
        target_size: int,
        overlap: int,
        embedding_model: str,
        config_hash: str,
        prefix_id: str = "",
        parent_id: str | None = None,
        start_idx: int = 0,
    ) -> list[ChunkRecord]:
        """Core chunking loop over sentence units."""
        chunks: list[ChunkRecord] = []
        chunk_idx = start_idx
        current_sentences: list[SentenceUnit] = []
        current_token_count = 0

        i = 0
        while i < len(sentence_units):
            unit = sentence_units[i]
            unit_tokens = unit["tokens"]

            if not current_sentences and unit_tokens >= target_size:
                current_sentences.append(unit)
                current_token_count += unit_tokens
                i += 1
            elif current_token_count + unit_tokens > target_size and current_sentences:
                chunk_record = self._build_chunk_record(
                    current_sentences,
                    doc=doc,
                    idx=chunk_idx,
                    token_count=current_token_count,
                    embedding_model=embedding_model,
                    config_hash=config_hash,
                    prefix_id=prefix_id,
                    parent_id=parent_id,
                )
                chunks.append(chunk_record)
                chunk_idx += 1

                overlap_sentences: list[SentenceUnit] = []
                overlap_tokens = 0
                for sent_unit in reversed(current_sentences):
                    s_tokens = sent_unit["tokens"]
                    if (overlap_tokens + s_tokens <= overlap) and (
                        len(overlap_sentences) + 1 < len(current_sentences)
                    ):
                        overlap_sentences.insert(0, sent_unit)
                        overlap_tokens += s_tokens
                    else:
                        break

                current_sentences = list(overlap_sentences)
                current_token_count = overlap_tokens
                continue
            else:
                current_sentences.append(unit)
                current_token_count += unit_tokens
                i += 1

        if current_sentences:
            chunk_record = self._build_chunk_record(
                current_sentences,
                doc=doc,
                idx=chunk_idx,
                token_count=current_token_count,
                embedding_model=embedding_model,
                config_hash=config_hash,
                prefix_id=prefix_id,
                parent_id=parent_id,
            )
            chunks.append(chunk_record)

        return chunks

    def _build_chunk_record(
        self,
        sentences: list[SentenceUnit],
        doc: ParsedDocument,
        idx: int,
        token_count: int,
        embedding_model: str,
        config_hash: str,
        prefix_id: str = "",
        parent_id: str | None = None,
    ) -> ChunkRecord:
        """Assemble ChunkRecord model from sentence units with optional contextual enrichment."""
        raw_text = " ".join(s["text"] for s in sentences)
        page_start = min(s["page"] for s in sentences)
        page_end = max(s["page"] for s in sentences)
        char_start = min(s["char_start"] for s in sentences)
        char_end = max(s["char_end"] for s in sentences)
        section = next((s["section_title"] for s in sentences if s["section_title"]), None)

        # Contextual enrichment prepends title/section context if enabled
        if self.config.contextual_enrichment:
            sec_label = section or "General"
            final_text = f"[Document: {doc.filename} | Section: {sec_label}]\n{raw_text}"
        else:
            final_text = raw_text

        chunk_id = f"{prefix_id}{doc.doc_id}_{idx:04d}"

        return ChunkRecord(
            chunk_id=chunk_id,
            doc_id=doc.doc_id,
            idx=idx,
            text=final_text,
            token_count=token_count,
            page_start=page_start,
            page_end=page_end,
            char_start=char_start,
            char_end=char_end,
            section_title=section,
            parent_id=parent_id,
            embedding_model=embedding_model,
            config_hash=config_hash,
        )
