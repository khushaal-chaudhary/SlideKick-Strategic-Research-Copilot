"""Namespace handling in the retriever's graph and vector queries."""

import copilot.graph.connection as connection_module
from copilot.agent.nodes.retrieval import _query_graph, _query_vector

NS = "test-workspace-1234"


def _patch_graph_query(monkeypatch, handler):
    calls: list[tuple[str, dict]] = []

    def query(cypher, params=None):
        calls.append((cypher, params))
        return handler(cypher, params)

    monkeypatch.setattr(connection_module.graph_connection, "query", query)
    return calls


class FakeEmbeddings:
    def __init__(self, *args, **kwargs):
        pass

    def embed_query(self, text):
        return [0.1] * 768


def test_query_graph_passes_namespace_to_all_queries(monkeypatch):
    calls = _patch_graph_query(monkeypatch, lambda c, p: [])

    _query_graph("Microsoft strategy overview", ["Microsoft"], namespace=NS)

    assert calls
    for cypher, params in calls:
        assert "(n.namespace IS NULL OR n.namespace = $ns)" in cypher
        assert params["ns"] == NS


def test_query_graph_without_namespace_sends_null(monkeypatch):
    calls = _patch_graph_query(monkeypatch, lambda c, p: [])

    _query_graph("Microsoft strategy overview", ["Microsoft"])

    assert all(params["ns"] is None for _, params in calls)


def test_query_vector_merges_user_and_demo_results_by_score(monkeypatch):
    import langchain_ollama

    monkeypatch.setattr(langchain_ollama, "OllamaEmbeddings", FakeEmbeddings)

    def handler(cypher, params):
        if "user_doc_embeddings" in cypher:
            assert params["ns"] == NS
            assert params["top_k"] == 20  # over-fetch: 5 * 4
            return [
                {"chunk_id": f"{NS}::a.txt::chunk_0", "text": "user", "source": "a.txt", "score": 0.95}
            ]
        return [
            {"chunk_id": "demo_1", "text": "demo", "source": "demo.pdf", "score": 0.80}
        ]

    _patch_graph_query(monkeypatch, handler)

    result = _query_vector("what is in my doc", top_k=5, namespace=NS)

    assert result["result_count"] == 2
    assert result["results"][0]["chunk_id"] == f"{NS}::a.txt::chunk_0"
    assert result["results"][1]["chunk_id"] == "demo_1"


def test_query_vector_survives_missing_user_index(monkeypatch):
    import langchain_ollama

    monkeypatch.setattr(langchain_ollama, "OllamaEmbeddings", FakeEmbeddings)

    def handler(cypher, params):
        if "user_doc_embeddings" in cypher:
            raise RuntimeError("no such index")
        return [{"chunk_id": "demo_1", "text": "demo", "source": "demo.pdf", "score": 0.80}]

    _patch_graph_query(monkeypatch, handler)

    result = _query_vector("query", top_k=5, namespace=NS)

    assert result["result_count"] == 1
    assert result["results"][0]["chunk_id"] == "demo_1"


def test_query_vector_skips_user_index_without_namespace(monkeypatch):
    import langchain_ollama

    monkeypatch.setattr(langchain_ollama, "OllamaEmbeddings", FakeEmbeddings)

    calls = _patch_graph_query(
        monkeypatch,
        lambda c, p: [{"chunk_id": "demo_1", "text": "demo", "source": "demo.pdf", "score": 0.8}],
    )

    _query_vector("query", top_k=5)

    assert all("user_doc_embeddings" not in cypher for cypher, _ in calls)
