"""Namespaced Neo4j writes for BYOD documents.

Every node written here carries a `namespace` property (the workspace id)
and a namespaced `id` (`<namespace>::<name>`), so user uploads live in the
same Aura database as the demo corpus without colliding with it: the demo
nodes have no namespace property and keep their original ids, and the
unique-id constraints stay satisfied.
"""

import logging
import time
from collections import defaultdict
from typing import Any

from copilot.ingestion.schema import ALLOWED_NODES, ALLOWED_RELATIONSHIPS

logger = logging.getLogger(__name__)

USER_VECTOR_INDEX = "user_doc_embeddings"

# Cypher labels/rel-types can't be parameterized; whitelist them instead.
_LABEL_BY_LOWER = {label.lower(): label for label in ALLOWED_NODES}
_RELS = set(ALLOWED_RELATIONSHIPS)


def namespaced_id(namespace: str, name: str) -> str:
    return f"{namespace}::{name}"


def write_graph_documents(graph, namespace: str, graph_documents: list) -> dict[str, int]:
    """Write extracted entities/relationships under the given namespace.

    Off-schema node labels and relationship types are dropped (strict
    schema enforcement at write time). Returns node/relationship counts.
    """
    now = time.time()
    nodes_by_label: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    node_label: dict[str, str] = {}

    for doc in graph_documents:
        for node in doc.nodes:
            label = _LABEL_BY_LOWER.get(str(node.type).lower())
            if not label or not node.id:
                continue
            name = str(node.id)
            nodes_by_label[label][name] = {
                "id": namespaced_id(namespace, name),
                "name": name,
                "namespace": namespace,
                "ns_created_at": now,
            }
            node_label[name] = label

    rels_by_type: dict[str, list[dict[str, str]]] = defaultdict(list)
    for doc in graph_documents:
        for rel in doc.relationships:
            rel_type = str(rel.type).upper()
            source, target = str(rel.source.id), str(rel.target.id)
            if rel_type not in _RELS or source not in node_label or target not in node_label:
                continue
            rels_by_type[rel_type].append(
                {
                    "source": namespaced_id(namespace, source),
                    "target": namespaced_id(namespace, target),
                }
            )

    total_nodes = 0
    for label, rows in nodes_by_label.items():
        graph.query(
            f"""
            UNWIND $rows AS row
            MERGE (n:`{label}` {{id: row.id}})
            SET n.name = row.name, n.namespace = row.namespace,
                n.ns_created_at = row.ns_created_at
            """,
            params={"rows": list(rows.values())},
        )
        total_nodes += len(rows)

    total_rels = 0
    for rel_type, rows in rels_by_type.items():
        graph.query(
            f"""
            UNWIND $rows AS row
            MATCH (a {{id: row.source}}), (b {{id: row.target}})
            MERGE (a)-[:`{rel_type}`]->(b)
            """,
            params={"rows": rows},
        )
        total_rels += len(rows)

    logger.info(
        "Wrote %d nodes, %d relationships for namespace %s", total_nodes, total_rels, namespace
    )
    return {"nodes": total_nodes, "relationships": total_rels}


def ensure_user_vector_index(graph, dimensions: int) -> None:
    graph.query(
        f"""
        CREATE VECTOR INDEX {USER_VECTOR_INDEX} IF NOT EXISTS
        FOR (c:UserChunk)
        ON c.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {int(dimensions)},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
    )


def write_vector_chunks(
    graph, namespace: str, source: str, texts: list[str], embeddings: list[list[float]]
) -> int:
    now = time.time()
    rows = [
        {
            "id": f"{namespace}::{source}::chunk_{i}",
            "text": text,
            "source": source,
            "namespace": namespace,
            "ns_created_at": now,
            "embedding": vector,
        }
        for i, (text, vector) in enumerate(zip(texts, embeddings))
    ]
    graph.query(
        """
        UNWIND $rows AS row
        MERGE (c:UserChunk {id: row.id})
        SET c.text = row.text, c.source = row.source, c.namespace = row.namespace,
            c.ns_created_at = row.ns_created_at, c.embedding = row.embedding
        """,
        params={"rows": rows},
    )
    return len(rows)


def purge_namespace(graph, namespace: str) -> int:
    result = graph.query(
        """
        MATCH (n) WHERE n.namespace = $ns
        DETACH DELETE n
        RETURN count(n) AS deleted
        """,
        params={"ns": namespace},
    )
    return result[0]["deleted"] if result else 0


def purge_expired(graph, ttl_hours: float = 24.0) -> int:
    cutoff = time.time() - ttl_hours * 3600
    result = graph.query(
        """
        MATCH (n) WHERE n.namespace IS NOT NULL AND n.ns_created_at < $cutoff
        DETACH DELETE n
        RETURN count(n) AS deleted
        """,
        params={"cutoff": cutoff},
    )
    return result[0]["deleted"] if result else 0
