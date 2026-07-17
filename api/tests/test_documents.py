"""Tests for the BYOD document upload endpoints."""

import json

import documents as documents_module

NS = "test-workspace-1234"


def _upload(client, filename="doc.txt", content=b"Some document text.", workspace_id=NS):
    return client.post(
        "/api/documents/upload",
        files={"file": (filename, content, "text/plain")},
        data={"workspace_id": workspace_id},
    )


def test_upload_rejects_bad_workspace_id(client):
    assert _upload(client, workspace_id="short").status_code == 400
    assert _upload(client, workspace_id="has spaces here").status_code == 400
    assert _upload(client, workspace_id="bad;DROP//injection").status_code == 400


def test_upload_rejects_unsupported_extension(client):
    response = _upload(client, filename="report.docx")
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file(client):
    assert _upload(client, content=b"").status_code == 400


def test_upload_rejects_oversized_file(client):
    too_big = b"x" * (documents_module.MAX_FILE_BYTES + 1)
    assert _upload(client, content=too_big).status_code == 413


def test_upload_starts_session_and_streams_completion(client, monkeypatch):
    import copilot.ingestion as ingestion_module

    def fake_ingest(workspace_id, filename, data, on_event=None):
        assert workspace_id == NS
        assert filename == "doc.txt"
        if on_event:
            on_event({"stage": "parsing", "message": "Parsing doc.txt..."})
        return {
            "workspace_id": workspace_id,
            "filename": filename,
            "nodes": 3,
            "relationships": 2,
            "chunks": 4,
            "skipped_chunks": 0,
        }

    monkeypatch.setattr(ingestion_module, "ingest_document", fake_ingest)

    response = _upload(client)
    assert response.status_code == 200
    body = response.json()
    assert body["workspace_id"] == NS
    assert body["stream_url"] == f"/api/documents/stream/{body['session_id']}"

    events = []
    with client.stream("GET", body["stream_url"]) as stream:
        for line in stream.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):]))

    types = [e["type"] for e in events]
    assert types[0] == "ingest_start"
    assert "ingest_progress" in types
    assert types[-1] == "ingest_complete"
    assert events[-1]["nodes"] == 3


def test_stream_unknown_session_404(client):
    assert client.get("/api/documents/stream/does-not-exist").status_code == 404


def test_delete_workspace(client, monkeypatch):
    import copilot.ingestion as ingestion_module

    monkeypatch.setattr(ingestion_module, "delete_workspace", lambda ws: 12)

    response = client.delete(f"/api/documents/{NS}")
    assert response.status_code == 200
    assert response.json() == {"workspace_id": NS, "deleted_nodes": 12}


def test_workspace_stats(client, monkeypatch):
    import copilot.ingestion as ingestion_module

    stats = {"workspace_id": NS, "documents": ["a.txt"], "entities": 5, "chunks": 3}
    monkeypatch.setattr(ingestion_module, "workspace_stats", lambda ws: stats)

    response = client.get(f"/api/documents/{NS}")
    assert response.status_code == 200
    assert response.json() == stats


def test_workspace_stats_rejects_bad_id(client):
    assert client.get("/api/documents/bad id!").status_code == 400
