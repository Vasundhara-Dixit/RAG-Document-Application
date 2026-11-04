"""Integration test for end-to-end ingestion, indexing, search, and reload."""

from pathlib import Path

from app.core.config import IndexingConfig
from app.indexing.chunker import SentenceTokenChunker
from app.indexing.embedder import MockEmbedder
from app.indexing.vector_store import DualVectorStore
from app.ingestion.cleaner import TextCleaner
from app.ingestion.parsers import DocumentParser


def test_end_to_end_ingestion_search_and_reload(tmp_path: Path) -> None:
    """Ingest fixture corpus, query index, delete document, and verify reload."""
    chroma_dir = tmp_path / "chroma"
    faiss_file = tmp_path / "faiss.index"
    idx_config = IndexingConfig(
        chroma_persist_dir=str(chroma_dir),
        chroma_collection_name="test_collection",
        faiss_index_path=str(faiss_file),
    )

    # 1. Initialize components
    parser = DocumentParser()
    cleaner = TextCleaner()
    chunker = SentenceTokenChunker()
    embedder = MockEmbedder()
    store = DualVectorStore(dimension=embedder.dimension, config=idx_config)

    assert store.count() == 0

    # 2. Ingest sample.txt
    sample_txt_path = Path("tests/fixtures/sample.txt")
    raw_txt_bytes = sample_txt_path.read_bytes()
    parsed_doc = parser.parse(
        raw_txt_bytes, sample_txt_path.name, "text/plain", "checksum_sample_txt"
    )
    cleaned_doc = cleaner.clean_document(parsed_doc)
    chunks = chunker.chunk(
        cleaned_doc, embedding_model=embedder.model_name, config_hash="test_hash"
    )

    assert len(chunks) > 0

    # 3. Embed and Index
    texts = [c.text for c in chunks]
    embeddings = embedder.embed_texts(texts)
    store.add(chunks, embeddings)

    assert store.count() == len(chunks)

    # 4. Search
    query = "What is the backup retention policy and disaster recovery RTO?"
    query_vec = embedder.embed_query(query)
    results = store.search(query_vec, top_k=3)

    assert len(results) > 0
    # Top result should have score in [-1.0, 1.0] (inner product on normalized vectors)
    top_score = results[0].score
    assert -1.0 <= top_score <= 1.0
    assert results[0].chunk.doc_id == cleaned_doc.doc_id

    # 5. Metadata filtering
    filtered_results = store.search(
        query_vec, top_k=3, filters={"doc_id": "non_existent"}
    )
    assert len(filtered_results) == 0

    matching_filtered = store.search(
        query_vec, top_k=3, filters={"doc_id": cleaned_doc.doc_id}
    )
    assert len(matching_filtered) > 0

    # 6. Simulate restart: instantiate a new DualVectorStore on same directory
    reloaded_store = DualVectorStore(dimension=embedder.dimension, config=idx_config)
    assert reloaded_store.count() == len(chunks)

    # Search reloaded index and verify matching results
    reloaded_results = reloaded_store.search(query_vec, top_k=3)
    assert len(reloaded_results) == len(results)
    assert reloaded_results[0].chunk.chunk_id == results[0].chunk.chunk_id

    # 7. Document Deletion
    deleted_count = reloaded_store.delete_by_doc_id(cleaned_doc.doc_id)
    assert deleted_count == len(chunks)
    assert reloaded_store.count() == 0

    empty_results = reloaded_store.search(query_vec, top_k=3)
    assert len(empty_results) == 0
