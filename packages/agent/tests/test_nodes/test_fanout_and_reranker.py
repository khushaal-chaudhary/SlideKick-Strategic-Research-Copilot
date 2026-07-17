"""Parallel retrieval fan-out merge semantics and cross-encoder reranking."""

import copilot.agent.nodes.retrieval.reranker as reranker_module
import copilot.agent.workflow as workflow_module
from copilot.agent.nodes.retrieval.reranker import rerank_node
from copilot.agent.state import create_initial_state


def test_parallel_fanout_merges_results_via_reducers(monkeypatch):
    """Hybrid strategy runs graph + vector concurrently; reducers merge deltas."""
    monkeypatch.setattr(
        workflow_module, "planner_node", lambda s: {"retrieval_strategy": "hybrid"}
    )
    monkeypatch.setattr(
        workflow_module,
        "graph_retrieval_node",
        lambda s: {
            "graph_results": [{"entity": "Microsoft", "types": ["Organization"]}],
            "all_retrievals": [{"source": "knowledge_graph"}],
        },
    )
    monkeypatch.setattr(
        workflow_module,
        "vector_retrieval_node",
        lambda s: {
            "vector_results": [{"text": "chunk", "score": 0.9, "source_type": "vector"}],
            "all_retrievals": [{"source": "vector_search"}],
        },
    )
    monkeypatch.setattr(workflow_module, "rerank_node", lambda s: {})
    monkeypatch.setattr(workflow_module, "analyzer_node", lambda s: {"synthesis": "x"})
    monkeypatch.setattr(
        workflow_module,
        "critic_node",
        lambda s: {"needs_refinement": False, "iteration": 1, "quality_score": 0.9},
    )
    monkeypatch.setattr(workflow_module, "generator_node", lambda s: {"output_content": "y"})
    monkeypatch.setattr(workflow_module, "responder_node", lambda s: {"final_response": "z"})

    agent = workflow_module.compile_research_agent()
    result = agent.invoke(create_initial_state("test query"))

    assert len(result["graph_results"]) == 1
    assert len(result["vector_results"]) == 1
    sources = {r["source"] for r in result["all_retrievals"]}
    assert sources == {"knowledge_graph", "vector_search"}
    assert result["final_response"] == "z"


class FakeCrossEncoder:
    """Scores candidates by how many words they share with the query."""

    def predict(self, pairs, **kwargs):
        return [
            len(set(q.lower().split()) & set(t.lower().split())) for q, t in pairs
        ]


def _state(**overrides):
    state = create_initial_state("Microsoft cloud revenue")
    state.update(overrides)
    return state


def test_rerank_orders_by_cross_encoder_score(monkeypatch):
    monkeypatch.setattr(reranker_module, "_get_model", lambda: FakeCrossEncoder())

    state = _state(
        vector_results=[
            {"text": "unrelated gardening tips", "score": 0.9},
            {"text": "Microsoft cloud revenue grew strongly", "score": 0.5},
        ],
        web_results=[{"title": "Microsoft", "content": "cloud news", "url": "u"}],
    )

    update = rerank_node(state)

    ranked = update["reranked_results"]
    assert ranked[0]["text"].startswith("Microsoft cloud revenue")
    assert ranked[0]["rerank_score"] >= ranked[-1]["rerank_score"]
    assert update["refinement_type"] == "none"
    assert update["refinement_focus"] == ""


def test_rerank_clips_to_top_n(monkeypatch):
    monkeypatch.setattr(reranker_module, "_get_model", lambda: FakeCrossEncoder())

    state = _state(
        vector_results=[{"text": f"chunk {i}", "score": 0.5} for i in range(40)]
    )

    update = rerank_node(state)
    assert len(update["reranked_results"]) == reranker_module.TOP_N


def test_rerank_without_model_passes_results_through(monkeypatch):
    monkeypatch.setattr(reranker_module, "_get_model", lambda: None)

    state = _state(vector_results=[{"text": "a chunk", "score": 0.5}])

    update = rerank_node(state)
    assert len(update["reranked_results"]) == 1
    assert update["reranked_results"][0]["rerank_score"] is None


def test_rerank_with_no_candidates_only_clears_refinement(monkeypatch):
    monkeypatch.setattr(reranker_module, "_get_model", lambda: FakeCrossEncoder())

    update = rerank_node(_state())

    assert "reranked_results" not in update
    assert update["refinement_type"] == "none"


def test_rerank_includes_graph_entities_and_relationships(monkeypatch):
    monkeypatch.setattr(reranker_module, "_get_model", lambda: FakeCrossEncoder())

    state = _state(
        graph_results=[
            {
                "entity": "Microsoft",
                "types": ["Organization"],
                "relationships": [{"rel": "HAS_REVENUE", "target": "$211B"}],
            },
            {"source": "Microsoft", "relationship": "PRODUCES", "target": "Azure"},
        ]
    )

    update = rerank_node(state)

    texts = [c["text"] for c in update["reranked_results"]]
    assert any("HAS_REVENUE" in t for t in texts)
    assert any("--[PRODUCES]-->" in t for t in texts)
