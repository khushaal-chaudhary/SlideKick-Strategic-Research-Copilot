"""
Neo4j database connection management.
"""

import logging
from functools import lru_cache
from typing import Any

from langchain_neo4j import Neo4jGraph

from copilot.config.settings import settings

logger = logging.getLogger(__name__)


class GraphConnection:
    """Managed Neo4j connection with lazy initialization."""

    def __init__(self) -> None:
        self._graph: Neo4jGraph | None = None

    @property
    def graph(self) -> Neo4jGraph:
        """Get or create the Neo4j connection."""
        if self._graph is None:
            self._connect()
        return self._graph  # type: ignore

    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        logger.info("🔌 Connecting to Neo4j...")
        try:
            self._graph = Neo4jGraph(
                url=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password_str,
            )
            self._graph.refresh_schema()
            logger.info("✅ Connected to Neo4j successfully.")
        except Exception as e:
            logger.error("❌ Failed to connect to Neo4j: %s", e)
            raise

    def refresh_schema(self) -> None:
        """Refresh the graph schema metadata."""
        self.graph.refresh_schema()

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a Cypher query."""
        return self.graph.query(cypher, params=params or {})

    def health_check(self) -> bool:
        """Check if the connection is healthy."""
        try:
            result = self.query("RETURN 'OK' AS status")
            return result[0]["status"] == "OK"
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False

    @property
    def schema(self) -> str:
        """Get the current graph schema as a string."""
        return self.graph.schema


@lru_cache
def get_graph_connection() -> GraphConnection:
    """Get the singleton graph connection."""
    return GraphConnection()


graph_connection = get_graph_connection()
