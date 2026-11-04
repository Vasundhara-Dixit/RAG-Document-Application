"""Unit tests for prompt builder and citation extraction."""

from app.core.config import GenerationConfig
from app.generation.prompts import PromptBuilder
from app.models.schemas import ChunkRecord, RetrievedPassage


def test_system_prompt_groundedness_contract() -> None:
    """Verify system prompt enforces context grounding and abstention message."""
    cfg = GenerationConfig(abstain_message="I do not have enough information.")
    builder = PromptBuilder(cfg)
    sys_prompt = builder.build_system_prompt()

    assert "ONLY the provided document passages" in sys_prompt
    assert "I do not have enough information." in sys_prompt
    assert "untrusted data" in sys_prompt


def test_user_prompt_token_budgeting() -> None:
    """Verify user prompt respects context token limits."""
    builder = PromptBuilder()
    passages: list[RetrievedPassage] = []

    for i in range(10):
        chunk = ChunkRecord(
            chunk_id=f"chk_{i}",
            doc_id="doc1",
            idx=i,
            text=f"Paragraph sentence number {i}. " * 30,
            token_count=120,
            page_start=1,
            page_end=1,
            char_start=0,
            char_end=200,
            embedding_model="mock",
            config_hash="h1",
        )
        passages.append(RetrievedPassage(chunk=chunk, score=0.9 - (i * 0.05)))

    # Limit to 500 context tokens
    prompt = builder.build_user_prompt(
        question="What is the summary?",
        passages=passages,
        max_context_tokens=500,
    )

    # Should contain first couple of chunks but not all 10
    assert "<context_passage_1>" in prompt
    assert "<context_passage_10>" not in prompt


def test_citation_extraction() -> None:
    """Verify regex citation extraction matches retrieved passages."""
    builder = PromptBuilder()
    chunk1 = ChunkRecord(
        chunk_id="chk_001",
        doc_id="doc_handbook",
        idx=0,
        text="The equipment allowance is $1000 for office furniture.",
        token_count=10,
        page_start=3,
        page_end=3,
        char_start=0,
        char_end=50,
        embedding_model="mock",
        config_hash="h1",
    )
    passages = [RetrievedPassage(chunk=chunk1, score=0.95)]
    doc_map = {"doc_handbook": "Employee_Handbook.pdf"}

    answer = (
        "Employees receive an equipment allowance of $1000 "
        "[Employee_Handbook.pdf, p.3]."
    )
    citations = builder.extract_citations(answer, passages, doc_map)

    assert len(citations) == 1
    assert citations[0].doc_id == "doc_handbook"
    assert citations[0].filename == "Employee_Handbook.pdf"
    assert citations[0].page == 3
    assert "equipment allowance" in citations[0].snippet


def test_abstention_detection() -> None:
    """Verify is_abstained accurately detects abstention formulations."""
    builder = PromptBuilder()
    assert builder.is_abstained(
        "The documents don't contain enough information to answer this."
    )
    assert builder.is_abstained(
        "I am sorry, the documents do not contain enough information."
    )
    assert not builder.is_abstained(
        "Backups run nightly at 02:00 UTC [manual.pdf, p.2]."
    )
