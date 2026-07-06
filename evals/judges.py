"""
LLM-as-judge scorers for agent-specific quality dimensions.

The judge model is Gemini (free tier) rather than the Groq Llama models the
agent itself runs on — judging with a different model family avoids
self-preference bias and keeps the demo's Groq quota untouched.

Standard RAG metrics (faithfulness, context precision) come from ragas in
run_evals.py; this module covers what ragas cannot express:
- fact recall against the golden dataset's expected facts
- a rubric-based answer quality score
"""

import json
import logging
import os
import re
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

# gemini: independent model family, but free tier caps at ~20 req/day.
# groq: shares the agent's Groq quota, so use a non-Llama model there
# (gpt-oss) to preserve the different-family judging property.
JUDGE_PROVIDER = os.environ.get("EVAL_JUDGE_PROVIDER", "gemini")
JUDGE_MODEL = os.environ.get(
    "EVAL_JUDGE_MODEL",
    "gemini-2.5-flash-lite" if JUDGE_PROVIDER == "gemini" else "openai/gpt-oss-120b",
)


FACT_RECALL_PROMPT = """You are an exacting evaluation judge. Given an answer produced by a research agent and a list of expected key facts, decide for EACH fact whether the answer contains it (semantically — exact wording is not required).

## Answer
{answer}

## Expected facts
{facts}

## Response format (JSON only, no markdown)
{{
  "facts": [
    {{"fact": "<the expected fact>", "present": true, "evidence": "<short quote from the answer, or empty>"}}
  ]
}}
"""

ANSWER_QUALITY_PROMPT = """You are an exacting evaluation judge for a research copilot. Score the answer to the query on each rubric dimension from 0.0 to 1.0.

## Query
{query}

## Query type
{query_type}

## Answer
{answer}

## Rubric
- relevance: does the answer address the query directly?
- completeness: does it cover the main aspects the query asks for?
- specificity: concrete facts, names, and details rather than generalities?
- coherence: well-structured, readable, non-repetitive?

## Response format (JSON only, no markdown)
{{
  "relevance": 0.0,
  "completeness": 0.0,
  "specificity": 0.0,
  "coherence": 0.0,
  "overall": 0.0,
  "reasoning": "<one or two sentences>"
}}
"""


@dataclass
class FactRecallResult:
    recall: float
    facts_present: list[dict]


@dataclass
class AnswerQualityResult:
    overall: float
    dimensions: dict
    reasoning: str


def get_judge_llm():
    if JUDGE_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=JUDGE_MODEL,
            temperature=0.0,
            api_key=os.environ["GROQ_API_KEY"],
        )
    return ChatGoogleGenerativeAI(
        model=JUDGE_MODEL,
        temperature=0.0,
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )


def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def judge_fact_recall(llm, answer: str, expected_facts: list[str]) -> FactRecallResult:
    if not expected_facts:
        return FactRecallResult(recall=1.0, facts_present=[])
    prompt = FACT_RECALL_PROMPT.format(
        answer=answer[:8000],
        facts="\n".join(f"- {f}" for f in expected_facts),
    )
    data = _parse_json(llm.invoke(prompt).content)
    facts = data.get("facts", [])
    present = sum(1 for f in facts if f.get("present"))
    recall = present / len(expected_facts) if expected_facts else 1.0
    return FactRecallResult(recall=min(recall, 1.0), facts_present=facts)


def judge_answer_quality(llm, query: str, query_type: str, answer: str) -> AnswerQualityResult:
    prompt = ANSWER_QUALITY_PROMPT.format(
        query=query, query_type=query_type, answer=answer[:8000]
    )
    data = _parse_json(llm.invoke(prompt).content)
    dims = {
        k: float(data.get(k, 0.0))
        for k in ("relevance", "completeness", "specificity", "coherence")
    }
    overall = float(data.get("overall", sum(dims.values()) / 4))
    return AnswerQualityResult(
        overall=max(0.0, min(overall, 1.0)),
        dimensions=dims,
        reasoning=str(data.get("reasoning", "")),
    )


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Correlation between the agent's self-assessed quality and the judge's score."""
    n = len(xs)
    if n < 3 or len(ys) != n:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy)
