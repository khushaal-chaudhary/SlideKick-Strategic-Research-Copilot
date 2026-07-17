"""Semantic vector-search retrieval node (Ollama embeddings + Neo4j index)."""

import logging
from typing import Any

from copilot.agent.state import ResearchState

logger = logging.getLogger(__name__)


def _query_vector(query: str, top_k: int = 5, namespace: str | None = None) -> dict[str, Any]:
    """
    Query vector embeddings for semantic similarity search.

    Uses Ollama embeddings (nomic-embed-text) + Neo4j vector index
    to find semantically similar document chunks. When a BYOD namespace
    is given, the user's uploaded chunks (user_doc_embeddings index) are
    searched too and merged with the demo corpus by score.

    Args:
        query: Search query
        top_k: Number of results to return
        namespace: Optional BYOD workspace id

    Returns:
        Dict with source, results (text passages), count, confidence
    """
    logger.info("   🔮 Executing vector search: '%s'", query[:60])

    try:
        from langchain_ollama import OllamaEmbeddings

        from copilot.graph.connection import graph_connection

        # Initialize embeddings (nomic-embed-text = 768 dimensions)
        embeddings = OllamaEmbeddings(model="nomic-embed-text")

        # Generate query embedding
        query_embedding = embeddings.embed_query(query)

        # Query Neo4j vector index
        cypher = """
            CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding)
            YIELD node, score
            RETURN
                node.id AS chunk_id,
                node.text AS text,
                node.source AS source,
                score
            ORDER BY score DESC
        """

        results = graph_connection.query(cypher, params={
            "embedding": query_embedding,
            "top_k": top_k,
        })

        if namespace:
            try:
                # Over-fetch: the index is shared by all workspaces and can't
                # pre-filter, so grab extra and filter to this namespace
                user_results = graph_connection.query(
                    """
                    CALL db.index.vector.queryNodes('user_doc_embeddings', $top_k, $embedding)
                    YIELD node, score
                    WHERE node.namespace = $ns
                    RETURN
                        node.id AS chunk_id,
                        node.text AS text,
                        node.source AS source,
                        score
                    ORDER BY score DESC
                    """,
                    params={
                        "embedding": query_embedding,
                        "top_k": top_k * 4,
                        "ns": namespace,
                    },
                )
                results = sorted(
                    results + user_results, key=lambda r: r.get("score", 0.0), reverse=True
                )[:top_k]
            except Exception as e:
                # Index doesn't exist until the first upload completes
                logger.info("   🔮 No user document index available: %s", str(e)[:100])

        # Format results
        formatted = []
        for r in results:
            formatted.append({
                "chunk_id": r.get("chunk_id"),
                "text": r.get("text", ""),
                "source": r.get("source", "unknown"),
                "score": r.get("score", 0.0),
                "source_type": "vector",
            })

        # Confidence based on top score
        top_score = formatted[0]["score"] if formatted else 0.0
        confidence = min(1.0, top_score)  # Score is already 0-1 for cosine

        logger.info("   🔮 Vector search found %d results (top score: %.3f)",
                   len(formatted), top_score)

        return {
            "source": "vector_search",
            "query": query,
            "results": formatted,
            "result_count": len(formatted),
            "confidence": confidence,
        }

    except ImportError as e:
        logger.warning("   ⚠️ langchain-ollama not installed: %s", e)
        return {
            "source": "vector_search",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": "langchain-ollama not installed. Run: pip install langchain-ollama",
        }
    except Exception as e:
        logger.error("   ❌ Vector search failed: %s", e)
        return {
            "source": "vector_search",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


def vector_retrieval_node(state: ResearchState) -> dict[str, Any]:
    """Run semantic search; return only new results (reducer appends)."""
    query = state.get("refinement_focus") or state["original_query"]

    logger.info("   🔮 Vector retrieval: '%s'", query[:60])
    result = _query_vector(query, namespace=state.get("workspace_id"))

    return {
        "vector_results": result["results"],
        "all_retrievals": [result],
    }
