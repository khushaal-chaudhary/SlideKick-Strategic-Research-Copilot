"""Bring-your-own-documents ingestion: parse, chunk, extract, embed, write."""

from copilot.ingestion.pipeline import (
    IngestionError,
    delete_workspace,
    ingest_document,
    purge_expired_workspaces,
    workspace_stats,
)

__all__ = [
    "IngestionError",
    "ingest_document",
    "delete_workspace",
    "purge_expired_workspaces",
    "workspace_stats",
]
