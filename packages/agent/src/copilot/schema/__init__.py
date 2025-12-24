"""
Schema package for Strategic Research Copilot.

This package defines the knowledge graph schema aligned with schema.org
and FIBO financial extensions.
"""

from copilot.schema.ontology import (
    NodeType,
    RelationType,
    SCHEMA_DEFINITIONS,
    MIGRATION_MAP,
    get_extraction_prompt,
    get_neo4j_schema,
    migrate_node_type,
    migrate_relationship_type,
)

__all__ = [
    "NodeType",
    "RelationType",
    "SCHEMA_DEFINITIONS",
    "MIGRATION_MAP",
    "get_extraction_prompt",
    "get_neo4j_schema",
    "migrate_node_type",
    "migrate_relationship_type",
]
