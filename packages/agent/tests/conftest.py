import os

# Must be set before any copilot import: settings are loaded at module import time
os.environ.setdefault("NEO4J_URI", "neo4j://localhost:7687")
os.environ.setdefault("NEO4J_PASSWORD", "test-password")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import pytest


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    """Stands in for a LangChain chat model: records prompts, returns canned responses."""

    def __init__(self, responses: list[str] | str):
        self.responses = [responses] if isinstance(responses, str) else list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        content = self.responses[min(len(self.prompts) - 1, len(self.responses) - 1)]
        return FakeResponse(content)


@pytest.fixture
def fake_llm_factory(monkeypatch):
    """Patch get_llm in a node module with a FakeLLM returning given responses."""

    def _install(module, responses):
        llm = FakeLLM(responses)
        monkeypatch.setattr(module, "get_llm", lambda temperature=None: llm)
        return llm

    return _install
