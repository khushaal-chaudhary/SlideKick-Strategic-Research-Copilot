"""
Bring-your-own-documents endpoints.

Upload a PDF/TXT/MD, watch the ingestion pipeline build a namespaced
knowledge (sub)graph over SSE, then query it alongside the demo corpus by
sending the same workspace_id with research queries.
"""

import asyncio
import json
import logging
import re
import threading
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from queue import Empty, Queue

from fastapi import APIRouter, Form, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md")
WORKSPACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")

# session_id -> {"queue": Queue, "workspace_id": str, "filename": str, "status": str}
ingest_sessions: dict[str, dict] = {}
ingest_sessions_lock = threading.Lock()


def _validate_workspace_id(workspace_id: str) -> str:
    if not WORKSPACE_ID_PATTERN.match(workspace_id):
        raise HTTPException(
            status_code=400,
            detail="workspace_id must be 8-64 characters of letters, digits, or hyphens",
        )
    return workspace_id


@router.post("/upload")
async def upload_document(file: UploadFile, workspace_id: str = Form(...)):
    """Accept a document and start background ingestion; stream progress via SSE."""
    _validate_workspace_id(workspace_id)

    filename = file.filename or "upload"
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data) // (1024 * 1024)} MB). Demo cap is 10 MB.",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    session_id = str(uuid.uuid4())
    event_queue: Queue = Queue()
    with ingest_sessions_lock:
        ingest_sessions[session_id] = {
            "queue": event_queue,
            "workspace_id": workspace_id,
            "filename": filename,
            "status": "pending",
        }

    def run_ingestion():
        try:
            from copilot.ingestion import ingest_document

            summary = ingest_document(
                workspace_id,
                filename,
                data,
                on_event=lambda event: event_queue.put(("progress", event)),
            )
            event_queue.put(("done", summary))
        except Exception as e:
            logger.error("Ingestion failed for %s: %s", filename, e)
            event_queue.put(("error", e))

    threading.Thread(target=run_ingestion, daemon=True).start()
    logger.info("Upload accepted: %s -> workspace %s (session %s)", filename, workspace_id, session_id)

    return {
        "session_id": session_id,
        "workspace_id": workspace_id,
        "filename": filename,
        "stream_url": f"/api/documents/stream/{session_id}",
    }


@router.get("/stream/{session_id}")
async def stream_ingestion(session_id: str):
    """SSE stream of ingestion progress events."""
    with ingest_sessions_lock:
        if session_id not in ingest_sessions:
            raise HTTPException(status_code=404, detail="Ingestion session not found")
        session = ingest_sessions[session_id]

    event_queue: Queue = session["queue"]

    def _sse(payload: dict) -> dict:
        payload["session_id"] = session_id
        payload["timestamp"] = datetime.utcnow().isoformat()
        return {"event": "message", "data": json.dumps(payload)}

    async def event_generator() -> AsyncGenerator[dict, None]:
        session["status"] = "processing"
        yield _sse(
            {
                "type": "ingest_start",
                "workspace_id": session["workspace_id"],
                "filename": session["filename"],
            }
        )
        while True:
            await asyncio.sleep(0.1)
            try:
                msg_type, payload = event_queue.get_nowait()
            except Empty:
                continue

            if msg_type == "progress":
                yield _sse({"type": "ingest_progress", **payload})
            elif msg_type == "done":
                session["status"] = "completed"
                yield _sse({"type": "ingest_complete", **payload})
                break
            elif msg_type == "error":
                session["status"] = "error"
                from main import _parse_rate_limit_error

                rate_limit_info = _parse_rate_limit_error(str(payload))
                error_payload = {"type": "error", "error": str(payload)}
                if rate_limit_info:
                    error_payload["error"] = (
                        f"Extraction model {rate_limit_info['limit_type_friendly'].lower()} reached — "
                        f"try again in {rate_limit_info['retry_after_friendly']}."
                    )
                    error_payload["error_type"] = "rate_limit"
                    error_payload["rate_limit"] = rate_limit_info
                yield _sse(error_payload)
                break

    return EventSourceResponse(event_generator())


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Stats for a workspace: uploaded documents, entity and chunk counts."""
    _validate_workspace_id(workspace_id)
    try:
        from copilot.ingestion import workspace_stats

        return workspace_stats(workspace_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workspace stats failed: %s", e)
        raise HTTPException(status_code=503, detail="Knowledge graph unavailable") from e


@router.delete("/{workspace_id}")
async def delete_workspace_endpoint(workspace_id: str):
    """Remove all data for a workspace."""
    _validate_workspace_id(workspace_id)
    try:
        from copilot.ingestion import delete_workspace

        deleted = delete_workspace(workspace_id)
        return {"workspace_id": workspace_id, "deleted_nodes": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workspace delete failed: %s", e)
        raise HTTPException(status_code=503, detail="Knowledge graph unavailable") from e
