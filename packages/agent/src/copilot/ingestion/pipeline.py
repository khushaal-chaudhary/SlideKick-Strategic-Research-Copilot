"""BYOD ingestion pipeline: parse -> chunk -> extract -> embed -> write."""

import logging
from collections.abc import Callable
from typing import Any

from copilot.graph.connection import graph_connection
from copilot.ingestion.chunker import extraction_chunks, vector_chunks
from copilot.ingestion.extractor import extract_graph_documents
from copilot.ingestion.parser import parse_file
from copilot.ingestion.writer import (
    ensure_user_vector_index,
    purge_expired,
    purge_namespace,
    write_graph_documents,
    write_vector_chunks,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], None]


class IngestionError(Exception):
    pass


def _notify(on_event: ProgressCallback | None, event: dict[str, Any]) -> None:
    if on_event:
        on_event(event)


def ingest_document(
    workspace_id: str,
    filename: str,
    data: bytes,
    on_event: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Ingest one uploaded document into the workspace's namespaced subgraph."""
    graph = graph_connection.graph

    _notify(on_event, {"stage": "parsing", "message": f"Parsing {filename}..."})
    try:
        text = parse_file(filename, data)
    except ValueError as e:
        raise IngestionError(str(e)) from e

    try:
        ext_chunks = extraction_chunks(text, source=filename)
    except ValueError as e:
        raise IngestionError(str(e)) from e
    vec_chunks = vector_chunks(text, source=filename)
    _notify(
        on_event,
        {
            "stage": "chunked",
            "message": f"Split into {len(ext_chunks)} extraction and {len(vec_chunks)} vector chunks",
            "extraction_chunks": len(ext_chunks),
            "vector_chunks": len(vec_chunks),
        },
    )

    def on_chunk(done: int, total: int) -> None:
        _notify(
            on_event,
            {
                "stage": "extracting",
                "message": f"Extracting entities: chunk {done}/{total}",
                "done": done,
                "total": total,
            },
        )

    graph_documents, skipped = extract_graph_documents(ext_chunks, on_progress=on_chunk)
    graph_counts = write_graph_documents(graph, workspace_id, graph_documents)
    _notify(
        on_event,
        {
            "stage": "graph_write",
            "message": (
                f"Knowledge graph updated: {graph_counts['nodes']} entities, "
                f"{graph_counts['relationships']} relationships"
            ),
            **graph_counts,
            "skipped_chunks": skipped,
        },
    )

    _notify(on_event, {"stage": "embedding", "message": f"Embedding {len(vec_chunks)} chunks..."})
    from langchain_ollama import OllamaEmbeddings

    from copilot.config.settings import settings

    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=settings.ollama_base_url)
    texts = [c.page_content for c in vec_chunks]
    vectors = embeddings.embed_documents(texts)
    ensure_user_vector_index(graph, dimensions=len(vectors[0]))
    chunk_count = write_vector_chunks(graph, workspace_id, filename, texts, vectors)

    summary = {
        "workspace_id": workspace_id,
        "filename": filename,
        "nodes": graph_counts["nodes"],
        "relationships": graph_counts["relationships"],
        "chunks": chunk_count,
        "skipped_chunks": skipped,
    }
    _notify(
        on_event,
        {
            "stage": "complete",
            "message": (
                f"Ingested {filename}: {summary['nodes']} entities, "
                f"{summary['relationships']} relationships, {chunk_count} searchable chunks"
            ),
            **summary,
        },
    )
    return summary


def delete_workspace(workspace_id: str) -> int:
    return purge_namespace(graph_connection.graph, workspace_id)


def purge_expired_workspaces(ttl_hours: float = 24.0) -> int:
    deleted = purge_expired(graph_connection.graph, ttl_hours)
    if deleted:
        logger.info("TTL purge removed %d expired BYOD nodes", deleted)
    return deleted


def workspace_stats(workspace_id: str) -> dict[str, Any]:
    graph = graph_connection.graph
    rows = graph.query(
        """
        MATCH (n) WHERE n.namespace = $ns
        RETURN count(n) AS total,
               count(CASE WHEN n:UserChunk THEN 1 END) AS chunks,
               collect(DISTINCT CASE WHEN n:UserChunk THEN n.source END) AS sources
        """,
        params={"ns": workspace_id},
    )
    row = rows[0] if rows else {"total": 0, "chunks": 0, "sources": []}
    sources = [s for s in row["sources"] if s]
    return {
        "workspace_id": workspace_id,
        "documents": sources,
        "entities": row["total"] - row["chunks"],
        "chunks": row["chunks"],
    }
