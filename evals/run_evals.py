"""
Eval harness for the SlideKick research agent.

Runs golden-dataset queries through the real LangGraph agent, then scores:
- faithfulness + context precision (ragas, Gemini judge)
- fact recall + rubric answer quality (hand-rolled judges, Gemini)
- critic calibration: Pearson correlation between the agent critic's own
  quality_score and the external judge's overall score

Usage:
    python evals/run_evals.py                # full dataset
    python evals/run_evals.py --subset 5     # first 5 queries
    python evals/run_evals.py --sleep 20     # extra Groq rate-limit headroom
    python evals/run_evals.py --start 9      # resume at q09, merging prior scores

Requires: NEO4J_URI/NEO4J_PASSWORD, GROQ_API_KEY, GOOGLE_API_KEY, TAVILY_API_KEY.
Writes evals/results/<date>.json and evals/results/latest.json.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(REPO_ROOT / "packages" / "agent" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from judges import (  # noqa: E402
    JUDGE_MODEL,
    JUDGE_PROVIDER,
    get_judge_llm,
    judge_answer_quality,
    judge_fact_recall,
    pearson,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("evals")

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_dataset(path: Path, subset: int | None) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[:subset] if subset else rows


# Judge-token budget: ragas context_precision makes one LLM call PER context,
# so uncapped context lists (30+) burn ~25k judge tokens per query and blow
# the Groq 200k TPD before the dataset finishes. Cap per source and clip.
MAX_GRAPH_CONTEXTS = 8
MAX_VECTOR_CONTEXTS = 4
MAX_WEB_CONTEXTS = 3
MAX_FINANCIAL_CONTEXTS = 2


def flatten_contexts(state: dict) -> list[str]:
    """Flatten the agent's heterogeneous retrieval results into ragas contexts."""
    contexts: list[str] = []
    for r in state.get("graph_results", [])[:MAX_GRAPH_CONTEXTS]:
        if "entity" in r:
            contexts.append(f"Graph entity: {r['entity']} (types: {r.get('types', [])})")
        elif "source" in r:
            contexts.append(
                f"Graph relationship: {r['source']} --[{r.get('relationship', '')}]--> {r.get('target', '')}"
            )
        else:
            contexts.append(json.dumps(r, default=str)[:300])
    for r in state.get("vector_results", [])[:MAX_VECTOR_CONTEXTS]:
        text = r.get("text", "")
        if text:
            contexts.append(f"Document chunk ({r.get('source', 'unknown')}): {text[:600]}")
    for r in state.get("web_results", [])[:MAX_WEB_CONTEXTS]:
        snippet = f"{r.get('title', '')}: {r.get('snippet', r.get('content', ''))}"
        contexts.append(f"Web result: {snippet[:500]}")
    if state.get("web_ai_answer"):
        contexts.append(f"Web AI summary: {state['web_ai_answer'][:800]}")
    for r in state.get("financial_results", [])[:MAX_FINANCIAL_CONTEXTS]:
        contexts.append(f"Financial data: {json.dumps(r, default=str)[:400]}")
    return contexts or ["(no retrieved context)"]


async def ragas_scores(judge_llm, query: str, answer: str, contexts: list[str]) -> dict:
    from ragas import SingleTurnSample
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference

    wrapper = LangchainLLMWrapper(judge_llm)
    sample = SingleTurnSample(user_input=query, response=answer, retrieved_contexts=contexts)
    scores = {}
    try:
        scores["faithfulness"] = await Faithfulness(llm=wrapper).single_turn_ascore(sample)
    except Exception as e:
        logger.warning("faithfulness failed: %s", e)
        scores["faithfulness"] = None
    try:
        scores["context_precision"] = await LLMContextPrecisionWithoutReference(
            llm=wrapper
        ).single_turn_ascore(sample)
    except Exception as e:
        logger.warning("context_precision failed: %s", e)
        scores["context_precision"] = None
    return scores


def mean(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def load_prior_results(start: int) -> dict[str, dict]:
    """For --start resumes, reuse scored per-query entries from the last run."""
    if start <= 1:
        return {}
    latest = RESULTS_DIR / "latest.json"
    if not latest.exists():
        logger.warning("--start %d but no latest.json to merge from", start)
        return {}
    prior = json.loads(latest.read_text(encoding="utf-8"))
    return {q["id"]: q for q in prior.get("per_query", []) if "scores" in q}


def run(dataset_path: Path, subset: int | None, sleep_s: float, start: int = 1) -> dict:
    from copilot.agent import create_copilot

    rows = load_dataset(dataset_path, subset)
    prior_by_id = load_prior_results(start)
    logger.info("Running %d eval queries (start=%d)", len(rows), start)

    copilot = create_copilot()
    judge_llm = get_judge_llm()

    per_query = []
    for i, row in enumerate(rows, 1):
        if i < start:
            reused = prior_by_id.get(row["id"])
            if reused:
                per_query.append(reused)
                logger.info("[%d/%d] reusing prior result for %s", i, len(rows), row["id"])
            else:
                logger.warning("[%d/%d] no prior scored result for %s; skipping", i, len(rows), row["id"])
            continue
        logger.info("[%d/%d] %s", i, len(rows), row["query"])
        started = time.time()
        try:
            state = copilot.research(row["query"])
        except Exception as e:
            logger.error("agent failed on %s: %s", row["id"], e)
            per_query.append({"id": row["id"], "query": row["query"], "error": str(e)})
            continue

        answer = state.get("final_response") or state.get("output_content") or ""
        contexts = flatten_contexts(state)

        rag = asyncio.run(ragas_scores(judge_llm, row["query"], answer, contexts))
        try:
            recall = judge_fact_recall(judge_llm, answer, row.get("expected_facts", []))
            quality = judge_answer_quality(
                judge_llm, row["query"], row.get("query_type", ""), answer
            )
        except Exception as e:
            logger.error("judge failed on %s: %s", row["id"], e)
            per_query.append({"id": row["id"], "query": row["query"], "error": f"judge: {e}"})
            continue

        per_query.append(
            {
                "id": row["id"],
                "query": row["query"],
                "query_type": row.get("query_type"),
                "answer_preview": answer[:400],
                "scores": {
                    "faithfulness": rag["faithfulness"],
                    "context_precision": rag["context_precision"],
                    "fact_recall": round(recall.recall, 4),
                    "answer_quality": round(quality.overall, 4),
                    "quality_dimensions": quality.dimensions,
                },
                "agent": {
                    "self_quality_score": state.get("quality_score"),
                    "iterations": state.get("iteration"),
                    "retrieval_strategy": state.get("retrieval_strategy"),
                    "output_format": state.get("output_format"),
                    "n_contexts": len(contexts),
                },
                "judge_reasoning": quality.reasoning,
                "latency_s": round(time.time() - started, 1),
            }
        )
        if i < len(rows):
            time.sleep(sleep_s)

    scored = [q for q in per_query if "scores" in q]
    self_scores = [q["agent"]["self_quality_score"] for q in scored
                   if q["agent"]["self_quality_score"] is not None]
    judge_scores = [q["scores"]["answer_quality"] for q in scored
                    if q["agent"]["self_quality_score"] is not None]

    return {
        "run_date": date.today().isoformat(),
        "timestamp": datetime.now(UTC).isoformat(),
        "judge_model": f"{JUDGE_PROVIDER}/{JUDGE_MODEL}",
        "agent_provider": os.environ.get("LLM_PROVIDER", "unset"),
        "n_queries": len(rows),
        "n_scored": len(scored),
        "n_errors": len(per_query) - len(scored),
        "aggregate": {
            "faithfulness": mean([q["scores"]["faithfulness"] for q in scored]),
            "context_precision": mean([q["scores"]["context_precision"] for q in scored]),
            "fact_recall": mean([q["scores"]["fact_recall"] for q in scored]),
            "answer_quality": mean([q["scores"]["answer_quality"] for q in scored]),
            "critic_calibration_pearson": (
                round(r, 4) if (r := pearson(self_scores, judge_scores)) is not None else None
            ),
            "avg_agent_self_score": mean(self_scores),
            "avg_iterations": mean([q["agent"]["iterations"] for q in scored]),
            "avg_latency_s": mean([q["latency_s"] for q in scored]),
        },
        "per_query": per_query,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", type=int, default=None, help="Run only the first N queries")
    parser.add_argument("--sleep", type=float, default=15.0, help="Seconds between queries")
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Resume from query N (1-based); earlier queries reuse scores from latest.json",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parent / "golden_dataset.jsonl",
    )
    args = parser.parse_args()

    results = run(args.dataset, args.subset, args.sleep, args.start)

    RESULTS_DIR.mkdir(exist_ok=True)
    dated = RESULTS_DIR / f"{results['run_date']}.json"
    payload = json.dumps(results, indent=2, default=str)
    dated.write_text(payload, encoding="utf-8")
    (RESULTS_DIR / "latest.json").write_text(payload, encoding="utf-8")
    logger.info("Wrote %s", dated)

    agg = results["aggregate"]
    print("\n=== Aggregate scores ===")
    for k, v in agg.items():
        print(f"  {k:32s} {v}")


if __name__ == "__main__":
    main()
