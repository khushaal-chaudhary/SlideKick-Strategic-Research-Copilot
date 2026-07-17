"""SQLite session snapshot persistence."""

import sessions as session_store
from schemas import SessionState


def _use_tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "DB_PATH", str(tmp_path / "sessions.db"))


def test_completed_session_roundtrip(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)

    session = SessionState(
        session_id="s1",
        query="What is Azure?",
        status="completed",
        final_response="Azure is Microsoft's cloud platform.",
    )
    session_store.save_session(session)

    loaded = session_store.load_session("s1")
    assert loaded is not None
    assert loaded.status == "completed"
    assert loaded.final_response == "Azure is Microsoft's cloud platform."
    assert loaded.query == "What is Azure?"


def test_interrupted_session_loads_as_error(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)

    session_store.save_session(
        SessionState(session_id="s2", query="q", status="processing")
    )

    loaded = session_store.load_session("s2")
    assert loaded.status == "error"
    assert "restart" in loaded.error


def test_unknown_session_returns_none(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)
    assert session_store.load_session("nope") is None


def test_purge_keeps_newest(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)

    for i in range(5):
        session_store.save_session(
            SessionState(session_id=f"p{i}", query="q", status="completed")
        )

    session_store.purge_old_sessions(keep=2)

    remaining = [
        sid for sid in (f"p{i}" for i in range(5))
        if session_store.load_session(sid) is not None
    ]
    assert len(remaining) == 2
