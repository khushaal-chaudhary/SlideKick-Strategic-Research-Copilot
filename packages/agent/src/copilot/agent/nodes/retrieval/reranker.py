"""
Cross-encoder reranking node.

Fan-in point after the parallel retrieval nodes. Merges the heterogeneous
results (graph / vector / web), scores each against the query with a local
cross-encoder (CPU, free), and writes a unified `reranked_results` view that
the analyzer consumes ahead of the raw per-source lists. Raw lists stay
untouched for observability.
"""

import logging
from typing import Any

from copilot.agent.state import RefinementType, ResearchState

logger = logging.getLogger(__name__)

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_N = 15

_model = None
_model_failed = False


def _get_model():
    global _model, _model_failed
    if _model is None and not _model_failed:
        try:
            from sentence_transformers import CrossEncoder

            _model = CrossEncoder(RERANK_MODEL)
        except Exception as e:
            logger.warning("Cross-encoder unavailable, skipping rerank: %s", e)
            _model_failed = True
    return _model


def _candidate_texts(state: ResearchState) -> list[dict[str, Any]]:
    """Flatten graph/vector/web results into scoreable text candidates."""
    candidates = []
    for r in state.get("graph_results", []):
        if "entity" in r:
            rels = ", ".join(
                f"{x.get('rel')}: {x.get('target')}"
                for x in r.get("relationships", [])
                if x and x.get("rel")
            )
            text = f"{r['entity']} ({', '.join(r.get('types', []))})"
            if rels:
                text += f" — {rels}"
        elif "source" in r and "relationship" in r:
            text = f"{r['source']} --[{r['relationship']}]--> {r.get('target', '')}"
        else:
            continue
        candidates.append({"source_type": "graph", "text": text, "result": r})

    for r in state.get("vector_results", []):
        if r.get("text"):
            candidates.append(
                {"source_type": "vector", "text": r["text"][:1000], "result": r}
            )

    for r in state.get("web_results", []):
        text = f"{r.get('title', '')}: {r.get('content', '')}"[:1000]
        if text.strip(": "):
            candidates.append({"source_type": "web", "text": text, "result": r})

    return candidates


def rerank_node(state: ResearchState) -> dict[str, Any]:
    """
    Rerank merged retrieval results with a cross-encoder.

    Also the join point of the retrieval fan-out: clears the critic's
    refinement request now that it has been executed.
    """
    update: dict[str, Any] = {
        "refinement_type": RefinementType.NONE.value,
        "refinement_focus": "",
    }

    candidates = _candidate_texts(state)
    if not candidates:
        return update

    query = state["original_query"]
    model = _get_model()

    if model is None:
        # No cross-encoder available — pass results through unranked
        update["reranked_results"] = [
            {**c, "rerank_score": None} for c in candidates[:TOP_N]
        ]
        return update

    try:
        scores = model.predict(
            [(query, c["text"]) for c in candidates], show_progress_bar=False
        )
    except Exception as e:
        logger.warning("Rerank scoring failed: %s", e)
        update["reranked_results"] = [
            {**c, "rerank_score": None} for c in candidates[:TOP_N]
        ]
        return update

    ranked = sorted(
        (
            {**c, "rerank_score": round(float(s), 4)}
            for c, s in zip(candidates, scores)
        ),
        key=lambda c: c["rerank_score"],
        reverse=True,
    )[:TOP_N]

    logger.info(
        "   🎯 Reranked %d candidates (top: %.3f '%s')",
        len(candidates),
        ranked[0]["rerank_score"],
        ranked[0]["text"][:60],
    )
    update["reranked_results"] = ranked
    return update
