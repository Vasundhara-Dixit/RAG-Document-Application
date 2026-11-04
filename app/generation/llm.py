"""LLM generation client supporting LiteLLM and deterministic offline mock."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.core.config import GenerationConfig, get_settings
from app.core.interfaces import LLM
from app.utils.logging import get_logger

logger = get_logger("llm")


class MockLLMClient(LLM):
    """Deterministic offline LLM for unit tests and offline environments."""

    def __init__(self, config: GenerationConfig | None = None) -> None:
        """Initialize mock LLM."""
        self.config = config or get_settings().generation

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Synthesize answer based on presence of context passages."""
        # Check if context contains passage text
        if "NO RELEVANT CONTEXT FOUND" in prompt or "<context_passage_1>" not in prompt:
            return self.config.abstain_message

        # Extract doc_id and page from the first passage header if present
        import re

        header_match = re.search(
            r"\[Source 1 \| Doc: ([^\|]+) \| Page: (\d+)\]", prompt
        )
        doc_id = header_match.group(1).strip() if header_match else "document"
        page = header_match.group(2).strip() if header_match else "1"

        # Extract question text to avoid false positives on context text
        q_match = re.search(r"QUESTION:\s*(.*?)(?:\n\nANSWER|$)", prompt, re.DOTALL)
        q_text = q_match.group(1).lower() if q_match else prompt.lower()

        # Extract context passage 1 text
        p_match = re.search(
            r"<context_passage_1>\s*(.*?)\s*</context_passage_1>",
            prompt,
            re.DOTALL,
        )
        passage_text = p_match.group(1) if p_match else ""

        # Extract query keywords
        q_words = re.findall(r"\b[a-zA-Z0-9_\$]+\b", q_text)
        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "of",
            "and",
            "in",
            "to",
            "for",
            "with",
            "at",
            "by",
            "from",
            "on",
            "are",
            "do",
            "does",
            "did",
            "how",
            "when",
            "where",
            "which",
            "who",
            "why",
            "can",
            "could",
            "will",
            "would",
            "should",
            "all",
            "any",
            "each",
            "or",
            "be",
            "this",
            "that",
            "these",
            "those",
            "about",
            "it",
            "tell",
            "me",
            "give",
            "explain",
            "document",
            "file",
        }
        keywords = {w for w in q_words if w not in stop_words and len(w) > 1}

        # Check if query is a general inquiry / overview / summary request
        general_triggers = [
            "what is this about",
            "what is this",
            "what is it about",
            "what's this about",
            "tell me about",
            "summarize",
            "summary",
            "overview",
            "explain this",
            "what does this document say",
            "what does this file say",
            "what is in this",
            "describe",
            "main point",
            "key point",
            "outline",
            "content",
            "what is it",
            "about",
        ]
        is_general_query = any(t in q_text for t in general_triggers)

        if passage_text:
            raw_sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", passage_text.strip())
                if len(s.strip()) > 10
            ]
            if not raw_sentences:
                raw_sentences = [passage_text.strip()[:200]]

            # General query synthesis from leading passage context
            if is_general_query or not keywords:
                selected = raw_sentences[:2] if len(raw_sentences) >= 2 else raw_sentences[:1]
                extracted = " ".join(selected)
                return f"{extracted} [{doc_id}, p.{page}]."

            # Specific query keyword matching
            best_sentences: list[str] = []
            best_score = 0

            for sent in raw_sentences:
                sent_clean = sent.lower()
                matches = sum(1 for kw in keywords if kw in sent_clean)
                if matches > best_score:
                    best_score = matches
                    best_sentences = [sent.strip()]
                elif matches == best_score and matches > 0 and len(best_sentences) < 2:
                    best_sentences.append(sent.strip())

            if best_score >= 1:
                extracted = " ".join(best_sentences)
                return f"{extracted} [{doc_id}, p.{page}]."

            # If scoped to document, provide context synthesis
            if "[scope:" in q_text or "[referenced" in q_text:
                extracted = " ".join(raw_sentences[:2])
                return f"{extracted} [{doc_id}, p.{page}]."

        # Explicit abstention if question is not answered by context
        return self.config.abstain_message

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Stream answer tokens synchronously."""
        full_text = self.generate(prompt, system_prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield token


class LiteLLMClient(LLM):
    """Production LLM client interfacing through LiteLLM."""

    def __init__(self, config: GenerationConfig | None = None) -> None:
        """Initialize LiteLLM client with configuration."""
        self.config = config or get_settings().generation

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate response with retries and exponential backoff."""
        import litellm

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response: Any = litellm.completion(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout_seconds,
                )
                content = str(response.choices[0].message.content or "")
                return content.strip()
            except Exception as e:
                last_error = e
                logger.warn(
                    "LiteLLM completion attempt failed",
                    attempt=attempt,
                    error=str(e),
                )
                if attempt < self.config.max_retries:
                    # Exponential backoff sleep
                    import time

                    time.sleep(2**attempt)

        retries = self.config.max_retries
        raise RuntimeError(
            f"LLM generation failed after {retries} attempts: {last_error}"
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Stream LLM response tokens via LiteLLM synchronous streaming."""
        import litellm

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = litellm.completion(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout_seconds,
                stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
        except Exception as e:
            logger.error("LiteLLM streaming failed", error=str(e))
            raise RuntimeError(f"Streaming failed: {e}") from e


def get_llm(
    config: GenerationConfig | None = None,
    force_mock: bool = False,
) -> LLM:
    """Return LLM instance; falls back to MockLLMClient if external APIs disallowed."""
    settings = get_settings()
    gen_config = config or settings.generation

    if force_mock or not settings.app.allow_external_llm:
        return MockLLMClient(gen_config)
    return LiteLLMClient(gen_config)
