import main as api_main


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_info(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "name" in resp.json() or "title" in resp.json() or resp.json()


def test_submit_query_creates_session(client):
    resp = client.post("/api/query", json={"query": "What is Microsoft's cloud strategy?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["stream_url"] == f"/api/stream/{body['session_id']}"
    with api_main.sessions_lock:
        assert body["session_id"] in api_main.sessions


def test_submit_query_rejects_missing_query(client):
    resp = client.post("/api/query", json={})
    assert resp.status_code == 422


def test_stream_unknown_session_404(client):
    resp = client.get("/api/stream/does-not-exist")
    assert resp.status_code == 404


def test_get_unknown_session_404(client):
    resp = client.get("/api/session/does-not-exist")
    assert resp.status_code == 404


def test_download_rejects_path_traversal(client):
    resp = client.get("/api/download/..%5Csecrets.pptx")
    assert resp.status_code == 400


def test_download_rejects_non_pptx(client):
    resp = client.get("/api/download/notes.txt")
    assert resp.status_code == 400


def test_download_missing_file_404(client):
    resp = client.get("/api/download/nonexistent.pptx")
    assert resp.status_code == 404
