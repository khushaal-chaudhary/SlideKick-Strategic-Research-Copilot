import os
import sys

# main.py imports `config`/`schemas` as top-level modules relative to api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("NEO4J_URI", "neo4j://localhost:7687")
os.environ.setdefault("NEO4J_PASSWORD", "test-password")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import main as api_main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with TestClient(api_main.app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_sessions():
    yield
    with api_main.sessions_lock:
        api_main.sessions.clear()
