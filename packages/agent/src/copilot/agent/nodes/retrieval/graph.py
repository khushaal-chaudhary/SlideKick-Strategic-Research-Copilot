"""Knowledge-graph retrieval node (Neo4j)."""

import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from copilot.agent.state import ResearchState

logger = logging.getLogger(__name__)


def _query_graph(query: str, entities: list[str], namespace: str | None = None) -> dict[str, Any]:
    """
    Query the Neo4j knowledge graph.

    Args:
        query: Search query
        entities: Specific entities to focus on
        namespace: Optional BYOD workspace id — includes that workspace's
            namespaced nodes alongside the demo corpus. When None, only the
            demo corpus (namespace IS NULL) is searched.

    Returns:
        Dict with source, results, count, and confidence
    """
    from copilot.graph.connection import graph_connection

    # Defense-in-depth: LLM-generated refinement queries are unbounded
    query = query[:500]
    entities = [e[:200] for e in entities if e]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _run_cypher(cypher, params):
        return graph_connection.query(cypher, params=params)

    results = []

    # `n.namespace = $ns` evaluates to null (falsy) when $ns is null,
    # so a single expression covers both the demo-only and BYOD cases.
    # Text chunks are excluded here — they belong to vector search.
    ns_filter = (
        "(n.namespace IS NULL OR n.namespace = $ns) "
        "AND NOT n:DocumentChunk AND NOT n:UserChunk"
    )

    try:
        # Strategy 1: Search by entities if we have them
        if entities:
            for entity in entities[:5]:  # Limit to avoid overquerying
                cypher = f"""
                    MATCH (n)-[r]-(m)
                    WHERE toLower(coalesce(n.name, n.id)) CONTAINS toLower($entity)
                      AND {ns_filter}
                    RETURN coalesce(n.name, n.id) AS source, type(r) AS relationship,
                           coalesce(m.name, m.id) AS target,
                           labels(n) AS source_type, labels(m) AS target_type
                    LIMIT 20
                """
                entity_results = _run_cypher(cypher, {"entity": entity, "ns": namespace})
                results.extend(entity_results)

        # Strategy 2: General search with key terms from query
        cypher = f"""
            MATCH (n)
            WHERE toLower(coalesce(n.name, n.id)) CONTAINS toLower($search)
              AND {ns_filter}
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN coalesce(n.name, n.id) AS entity, labels(n) AS types,
                   collect(DISTINCT {{rel: type(r), target: coalesce(m.name, m.id)}})[..5] AS relationships
            LIMIT 30
        """
        search_terms = query.lower().split()[:3]
        for term in search_terms:
            if len(term) > 3:
                query_results = _run_cypher(cypher, {"search": term, "ns": namespace})
                results.extend(query_results)

        # Deduplicate
        seen = set()
        unique_results = []
        for r in results:
            key = str(r.get("entity", r.get("source", "")))
            if key and key not in seen:
                seen.add(key)
                unique_results.append(r)

        confidence = min(1.0, len(unique_results) / 10)

        return {
            "source": "knowledge_graph",
            "query": query,
            "results": unique_results[:30],
            "result_count": len(unique_results),
            "confidence": confidence,
        }

    except Exception as e:
        logger.error("Graph query failed: %s", e)
        return {
            "source": "knowledge_graph",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


def graph_retrieval_node(state: ResearchState) -> dict[str, Any]:
    """Query the knowledge graph; return only new results (reducer appends)."""
    query = state.get("refinement_focus") or state["original_query"]
    entities = list(state.get("entities_of_interest", []))
    if state.get("refinement_focus"):
        entities.append(state["refinement_focus"])

    logger.info("   📚 Graph retrieval: '%s'", query[:60])
    result = _query_graph(query, entities, namespace=state.get("workspace_id"))

    return {
        "graph_results": result["results"],
        "all_retrievals": [result],
    }
