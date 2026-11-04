"""Unit tests for sentence-boundary token chunker."""

from app.core.config import ChunkingConfig
from app.indexing.chunker import SentenceTokenChunker
from app.models.schemas import ParsedDocument, ParsedPage


def test_chunker_sentence_boundary_preservation() -> None:
    """Verify chunker respects sentence boundaries and doesn't cut mid-sentence."""
    config = ChunkingConfig(chunk_size=30, chunk_overlap=10)
    chunker = SentenceTokenChunker(config)

    text = (
        "The quick brown fox jumps over the lazy dog. "
        "Artificial intelligence is transforming software engineering. "
        "Retrieval augmented generation provides grounded answers with citations. "
        "Deterministic evaluation is essential for production systems."
    )
    doc = ParsedDocument(
        doc_id="doc_test",
        filename="test.txt",
        mime="text/plain",
        checksum="chk123",
        pages=[
            ParsedPage(
                page_number=1, text=text, char_offset_start=0, char_offset_end=len(text)
            )
        ],
        total_pages=1,
    )

    chunks = chunker.chunk(
        doc, embedding_model="text-embedding-3-small", config_hash="hash123"
    )
    assert len(chunks) >= 2

    for c in chunks:
        # Every chunk should start and end with complete words and sentences
        assert c.text[0].isupper()
        assert c.text.endswith(".")
        assert c.token_count <= 40  # reasonable boundary margin for sentence unit
        assert c.embedding_model == "text-embedding-3-small"
        assert c.config_hash == "hash123"
        assert c.doc_id == "doc_test"


def test_chunker_multi_page_provenance() -> None:
    """Verify page tracking when sentences span multiple pages."""
    config = ChunkingConfig(chunk_size=50, chunk_overlap=15)
    chunker = SentenceTokenChunker(config)

    p1_text = (
        "This is the first sentence on page one. "
        "Here is the second sentence on page one."
    )
    p2_text = (
        "This is a follow up sentence appearing on page two. "
        "Final sentence on page two."
    )

    doc = ParsedDocument(
        doc_id="doc_multi",
        filename="multi.txt",
        mime="text/plain",
        checksum="c456",
        pages=[
            ParsedPage(
                page_number=1,
                text=p1_text,
                char_offset_start=0,
                char_offset_end=len(p1_text),
            ),
            ParsedPage(
                page_number=2,
                text=p2_text,
                char_offset_start=len(p1_text) + 1,
                char_offset_end=len(p1_text) + 1 + len(p2_text),
            ),
        ],
        total_pages=2,
    )

    chunks = chunker.chunk(doc, embedding_model="mock", config_hash="hash")
    assert len(chunks) >= 1
    # Check that page_start and page_end are valid integers
    for c in chunks:
        assert 1 <= c.page_start <= 2
        assert 1 <= c.page_end <= 2
        assert c.page_start <= c.page_end


def test_chunker_handles_large_code_blocks_without_infinite_loop() -> None:
    """Verify chunker cleanly handles multi-line SQL/code blocks that exceed target size."""
    config = ChunkingConfig(chunk_size=50, chunk_overlap=10)
    chunker = SentenceTokenChunker(config)

    # Multi-line text with no standard sentence punctuation
    lines = [f"INSERT INTO table_name VALUES ({i}, 'sample_data_{i}');" for i in range(100)]
    large_block = "\n".join(lines)

    doc = ParsedDocument(
        doc_id="doc_sql",
        filename="query.sql",
        mime="text/plain",
        checksum="sql123",
        pages=[
            ParsedPage(
                page_number=1,
                text=large_block,
                char_offset_start=0,
                char_offset_end=len(large_block),
            )
        ],
        total_pages=1,
    )

    chunks = chunker.chunk(doc, embedding_model="mock", config_hash="hash")
    assert len(chunks) > 1
    # Verify every chunk was produced without freezing and has valid metadata
    for c in chunks:
        assert len(c.text) > 0
        assert c.token_count > 0
