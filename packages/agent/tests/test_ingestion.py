"""Unit tests for the BYOD ingestion package (no Neo4j / LLM needed)."""

from types import SimpleNamespace

import pytest

from copilot.ingestion.chunker import (
    MAX_EXTRACTION_CHUNKS,
    DocumentTooLargeError,
    extraction_chunks,
    vector_chunks,
)
from copilot.ingestion.parser import UnsupportedFileError, parse_file
from copilot.ingestion.writer import (
    namespaced_id,
    purge_expired,
    purge_namespace,
    write_graph_documents,
    write_vector_chunks,
)

NS = "test-workspace-1234"


class FakeGraph:
    """Records Cypher queries; returns canned results."""

    def __init__(self, results=None):
        self.calls: list[tuple[str, dict | None]] = []
        self._results = results if results is not None else []

    def query(self, cypher, params=None):
        self.calls.append((cypher, params))
        return self._results


def _node(name, label):
    return SimpleNamespace(id=name, type=label)


def _rel(source, rel_type, target):
    return SimpleNamespace(
        source=SimpleNamespace(id=source),
        target=SimpleNamespace(id=target),
        type=rel_type,
    )


def _graph_doc(nodes, relationships):
    return SimpleNamespace(nodes=nodes, relationships=relationships)


# =============================================================================
# Parser
# =============================================================================


def test_parse_txt_decodes_utf8():
    assert parse_file("notes.txt", "hello café".encode()) == "hello café"


def test_parse_md_supported():
    assert "# Title" in parse_file("readme.md", b"# Title\n\nBody")


def test_parse_unsupported_extension_raises():
    with pytest.raises(UnsupportedFileError):
        parse_file("data.docx", b"whatever")


# =============================================================================
# Chunker
# =============================================================================


def test_small_text_single_chunk_with_source():
    docs = extraction_chunks("short text", source="a.txt")
    assert len(docs) == 1
    assert docs[0].metadata["source"] == "a.txt"


def test_extraction_chunk_cap_enforced():
    huge = "word " * (MAX_EXTRACTION_CHUNKS * 500)
    with pytest.raises(DocumentTooLargeError):
        extraction_chunks(huge, source="huge.txt")


def test_vector_chunks_smaller_than_extraction_chunks():
    text = "para. " * 2000
    assert len(vector_chunks(text, source="a.txt")) >= len(
        extraction_chunks(text, source="a.txt")
    )


# =============================================================================
# Writer
# =============================================================================


def test_write_graph_documents_namespaces_ids_and_counts():
    graph = FakeGraph()
    doc = _graph_doc(
        nodes=[_node("Microsoft", "Organization"), _node("Azure", "Product")],
        relationships=[_rel("Microsoft", "PRODUCES", "Azure")],
    )

    counts = write_graph_documents(graph, NS, [doc])

    assert counts == {"nodes": 2, "relationships": 1}
    node_rows = [
        row
        for cypher, params in graph.calls
        if "MERGE (n:" in cypher
        for row in params["rows"]
    ]
    ids = {row["id"] for row in node_rows}
    assert ids == {f"{NS}::Microsoft", f"{NS}::Azure"}
    assert all(row["namespace"] == NS for row in node_rows)
    assert all("ns_created_at" in row for row in node_rows)


def test_write_graph_documents_drops_off_schema_labels_and_rels():
    graph = FakeGraph()
    doc = _graph_doc(
        nodes=[_node("Microsoft", "Organization"), _node("World Peace", "Mission")],
        relationships=[
            _rel("Microsoft", "PURSUES", "World Peace"),  # off-schema rel type
            _rel("Microsoft", "PRODUCES", "World Peace"),  # target node dropped
        ],
    )

    counts = write_graph_documents(graph, NS, [doc])

    assert counts == {"nodes": 1, "relationships": 0}
    assert not any("Mission" in cypher for cypher, _ in graph.calls)


def test_write_graph_documents_normalizes_label_casing():
    graph = FakeGraph()
    doc = _graph_doc(nodes=[_node("$10B", "Monetaryamount")], relationships=[])

    counts = write_graph_documents(graph, NS, [doc])

    assert counts["nodes"] == 1
    assert any("`MonetaryAmount`" in cypher for cypher, _ in graph.calls)


def test_write_vector_chunks_ids_and_count():
    graph = FakeGraph()
    count = write_vector_chunks(
        graph, NS, "a.txt", ["chunk one", "chunk two"], [[0.1], [0.2]]
    )

    assert count == 2
    _, params = graph.calls[0]
    assert params["rows"][0]["id"] == f"{NS}::a.txt::chunk_0"
    assert params["rows"][1]["embedding"] == [0.2]
    assert all(row["namespace"] == NS for row in params["rows"])


def test_purge_namespace_returns_deleted_count():
    graph = FakeGraph(results=[{"deleted": 7}])
    assert purge_namespace(graph, NS) == 7
    _, params = graph.calls[0]
    assert params == {"ns": NS}


def test_purge_expired_only_targets_namespaced_nodes():
    graph = FakeGraph(results=[{"deleted": 3}])
    assert purge_expired(graph, ttl_hours=24) == 3
    cypher, params = graph.calls[0]
    assert "n.namespace IS NOT NULL" in cypher
    assert "cutoff" in params


def test_namespaced_id_format():
    assert namespaced_id("ws", "Entity Name") == "ws::Entity Name"
