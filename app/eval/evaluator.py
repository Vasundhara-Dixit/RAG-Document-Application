"""Answer evaluator combining embedding semantic similarity and LLM-as-judge scoring."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import EvalConfig, get_settings
from app.core.interfaces import Embedder
from app.generation.llm import get_llm
from app.models.schemas import RetrievedPassage
from app.utils.logging import get_logger

logger = get_logger("evaluator")


@dataclass
class AnswerEvaluationResult:
    """Quantitative scoring result for a single synthesized answer."""

    item_id: str
    question: str
    generated_answer: str
    reference_answer: str
    semantic_similarity: float
    faithfulness: float
    correctness: float
    completeness: float
    reasoning: str


JUDGE_SYSTEM_PROMPT = """You are an impartial, highly rigorous evaluation judge assessing a RAG question-answering system.
You will be provided with:
1. The user's Question.
2. The Retrieved Context passages that the system was given.
3. The Reference Answer (ground truth).
4. The System's Generated Answer.

Score the generated answer on three criteria on an integer scale from 1 to 5:
- faithfulness: (1-5) Are all claims in the generated answer strictly supported by the retrieved context? (5 = entirely supported; 1 = complete hallucination or fabrications).
- correctness: (1-5) How accurately does the generated answer match the factual meaning of the Reference Answer? (5 = completely accurate; 1 = wrong or contradictory).
- completeness: (1-5) Does the generated answer address all key aspects of the question? (5 = thoroughly answers all parts; 1 = completely missed the question).

If the reference answer indicates that the question cannot be answered from the documents, and the system faithfully stated that it doesn't have enough information, assign 5 for faithfulness, correctness, and completeness.

You MUST respond ONLY with valid JSON in the exact format:
{
  "faithfulness": <1-5>,
  "correctness": <1-5>,
  "completeness": <1-5>,
  "reasoning": "<concise justification>"
}"""


class AnswerEvaluator:
    """Evaluates generated answers against ground-truth references and retrieved passages."""

    def __init__(
        self,
        embedder: Embedder,
        config: EvalConfig | None = None,
    ) -> None:
        """Initialize answer evaluator with embedder and judge settings."""
        self.embedder = embedder
        self.config = config or get_settings().eval
        self.llm = get_llm()

    def compute_semantic_similarity(
        self,
        generated_answer: str,
        reference_answer: str,
    ) -> float:
        """Calculate cosine similarity between generated answer and reference answer."""
        gen_clean = generated_answer.strip().lower()
        ref_clean = reference_answer.strip().lower()

        # Check for abstention alignment
        abstain_phrases = [
            "don't contain enough information",
            "do not contain enough information",
            "not enough information",
            "cannot be answered",
        ]
        gen_abstained = any(p in gen_clean for p in abstain_phrases)
        ref_abstained = any(p in ref_clean for p in abstain_phrases)

        if gen_abstained and ref_abstained:
            return 1.0
        if gen_abstained != ref_abstained:
            return 0.0

        if not gen_clean or not ref_clean:
            return 0.0

        # Embed both texts and compute dot product of L2-normalized vectors
        embeddings = self.embedder.embed_texts([generated_answer, reference_answer])
        vec_gen, vec_ref = embeddings[0], embeddings[1]

        # Inner product of normalized vectors
        dot_product = sum(a * b for a, b in zip(vec_gen, vec_ref, strict=True))
        # Clamp to [0.0, 1.0]
        similarity = max(0.0, min(1.0, dot_product))
        return round(similarity, 4)

    def evaluate_with_judge(
        self,
        question: str,
        contexts: list[RetrievedPassage],
        generated_answer: str,
        reference_answer: str,
    ) -> tuple[float, float, float, str]:
        """Query LLM judge to evaluate faithfulness, correctness, and completeness."""
        settings = get_settings()

        # If running in offline mode or external LLM not allowed, compute deterministic heuristic scores
        if not settings.app.allow_external_llm:
            return self._offline_judge(
                question=question,
                contexts=contexts,
                generated_answer=generated_answer,
                reference_answer=reference_answer,
            )

        context_text = "\n\n".join(
            f"Passage {i + 1} [Doc: {c.chunk.doc_id}, Page: {c.chunk.page_start}]:\n{c.chunk.text}"
            for i, c in enumerate(contexts)
        )

        user_prompt = (
            f"QUESTION:\n{question}\n\n"
            f"RETRIEVED CONTEXT:\n{context_text or 'None'}\n\n"
            f"REFERENCE ANSWER:\n{reference_answer}\n\n"
            f"GENERATED ANSWER:\n{generated_answer}\n\n"
            f"Provide your JSON assessment."
        )

        try:
            import litellm

            response: Any = litellm.completion(
                model=self.config.judge_model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.judge_temperature,
                response_format={"type": "json_object"},
            )
            content = str(response.choices[0].message.content or "{}")
            return self._parse_judge_json(content)
        except Exception as e:
            logger.warn(
                "Online LLM judge evaluation failed, falling back to heuristic",
                error=str(e),
            )
            return self._offline_judge(
                question=question,
                contexts=contexts,
                generated_answer=generated_answer,
                reference_answer=reference_answer,
            )

    def _parse_judge_json(self, raw_json: str) -> tuple[float, float, float, str]:
        """Parse structured rubric scores (1-5 scale mapped to 0.0-1.0)."""
        clean_str = raw_json.strip()
        match = re.search(r"\{.*\}", clean_str, re.DOTALL)
        if match:
            clean_str = match.group(0)

        data = json.loads(clean_str)
        f_raw = float(data.get("faithfulness", 3))
        c_raw = float(data.get("correctness", 3))
        comp_raw = float(data.get("completeness", 3))
        reason = str(data.get("reasoning", "LLM-as-judge evaluation"))

        # Map 1-5 scale to 0.0 - 1.0 (1 -> 0.0, 5 -> 1.0)
        f_norm = round(max(0.0, min(1.0, (f_raw - 1.0) / 4.0)), 4)
        c_norm = round(max(0.0, min(1.0, (c_raw - 1.0) / 4.0)), 4)
        comp_norm = round(max(0.0, min(1.0, (comp_raw - 1.0) / 4.0)), 4)

        return f_norm, c_norm, comp_norm, reason

    def _offline_judge(
        self,
        question: str,
        contexts: list[RetrievedPassage],
        generated_answer: str,
        reference_answer: str,
    ) -> tuple[float, float, float, str]:
        """Deterministic offline assessment when external LLM calls are disabled."""
        gen_clean = generated_answer.strip().lower()
        ref_clean = reference_answer.strip().lower()

        abstain_phrases = [
            "don't contain enough information",
            "do not contain enough information",
            "not enough information",
        ]
        gen_abs = any(p in gen_clean for p in abstain_phrases)
        ref_abs = any(p in ref_clean for p in abstain_phrases)

        # 1. Abstention handling
        if ref_abs:
            if gen_abs:
                return 1.0, 1.0, 1.0, "Properly abstained on out-of-domain query."
            return 0.2, 0.0, 0.2, "Failed to abstain when context is insufficient."

        # If model abstained on a question with an answer
        if gen_abs and not ref_abs:
            return 1.0, 0.0, 0.0, "Model incorrectly abstained on answerable question."

        # 2. Token overlap and claim coverage against reference answer
        def tokenize(text: str) -> set[str]:
            # Strip citation brackets before extracting claim words
            clean_text = re.sub(r"\[[^\]]+\]", "", text)
            words = re.findall(r"\b\w+\b", clean_text.lower())
            stop_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "of",
                "and",
                "in",
                "to",
                "for",
                "with",
                "at",
                "by",
                "on",
            }
            return {w for w in words if w not in stop_words}

        gen_tokens = tokenize(generated_answer)
        ref_tokens = tokenize(reference_answer)

        if not ref_tokens:
            return 0.5, 0.5, 0.5, "Reference answer contained no keywords."

        intersection = gen_tokens.intersection(ref_tokens)
        token_recall = len(intersection) / len(ref_tokens)
        token_precision = len(intersection) / len(gen_tokens) if gen_tokens else 0.0
        f1 = (
            2 * token_precision * token_recall / (token_precision + token_recall)
            if (token_precision + token_recall) > 0
            else 0.0
        )

        # 3. Faithfulness: check if claims in generated answer appear in context
        all_context_text = " ".join(c.chunk.text.lower() for c in contexts)
        context_tokens = tokenize(all_context_text)
        grounded_tokens = gen_tokens.intersection(context_tokens)
        faithfulness = len(grounded_tokens) / len(gen_tokens) if gen_tokens else 1.0

        correctness = round(f1, 4)
        completeness = round(token_recall, 4)
        faithfulness = round(faithfulness, 4)
        reason = f"Offline token evaluation (overlap: {len(intersection)}/{len(ref_tokens)} keywords)"

        return faithfulness, correctness, completeness, reason

    def evaluate_answer(
        self,
        item_id: str,
        question: str,
        contexts: list[RetrievedPassage],
        generated_answer: str,
        reference_answer: str,
    ) -> AnswerEvaluationResult:
        """Run full evaluation suite on a generated answer."""
        similarity = self.compute_semantic_similarity(
            generated_answer=generated_answer,
            reference_answer=reference_answer,
        )
        faith, corr, comp, reason = self.evaluate_with_judge(
            question=question,
            contexts=contexts,
            generated_answer=generated_answer,
            reference_answer=reference_answer,
        )

        return AnswerEvaluationResult(
            item_id=item_id,
            question=question,
            generated_answer=generated_answer,
            reference_answer=reference_answer,
            semantic_similarity=similarity,
            faithfulness=faith,
            correctness=corr,
            completeness=comp,
            reasoning=reason,
        )
