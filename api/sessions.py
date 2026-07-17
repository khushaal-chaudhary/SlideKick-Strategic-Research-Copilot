"""
SQLite-backed session persistence.

The in-memory `sessions` dict in main.py stays the hot path (SSE handlers
mutate live SessionState objects); this store snapshots sessions to disk at
lifecycle transitions so `GET /api/session/{id}` survives process restarts.
SSE queues are per-request and intentionally not persisted.
"""

import logging
import os
import sqlite3
import threading

from schemas import SessionState

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "SESSIONS_DB_PATH",
    os.path.join(os.path.dirname(__file__), "sessions.db"),
)

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload TEXT NOT NULL
        )
        """
    )
    return conn


def save_session(session: SessionState) -> None:
    """Upsert a snapshot of the session. Failures are non-fatal."""
    try:
        with _lock, _connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, status, created_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    status = excluded.status,
                    payload = excluded.payload
                """,
                (
                    session.session_id,
                    session.status,
                    session.created_at.isoformat(),
                    session.model_dump_json(exclude={"events"}),
                ),
            )
    except Exception as e:
        logger.warning("Session persistence failed (non-fatal): %s", e)


def load_session(session_id: str) -> SessionState | None:
    """Load a persisted session, or None if unknown/unreadable."""
    try:
        with _lock, _connect() as conn:
            row = conn.execute(
                "SELECT payload FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        session = SessionState.model_validate_json(row[0])
        # A session interrupted by a restart can never complete
        if session.status in ("pending", "processing"):
            session.status = "error"
            session.error = "Session was interrupted by a server restart."
        return session
    except Exception as e:
        logger.warning("Session load failed (non-fatal): %s", e)
        return None


def purge_old_sessions(keep: int = 500) -> None:
    """Keep the newest `keep` sessions; delete the rest."""
    try:
        with _lock, _connect() as conn:
            conn.execute(
                """
                DELETE FROM sessions WHERE session_id NOT IN (
                    SELECT session_id FROM sessions
                    ORDER BY created_at DESC LIMIT ?
                )
                """,
                (keep,),
            )
    except Exception as e:
        logger.warning("Session purge failed (non-fatal): %s", e)
