"""
Strategic Research Copilot

An AI research analyst that:
- Plans multi-step research approaches
- Retrieves data from knowledge graphs, vectors, and web
- Analyzes and synthesizes insights
- Self-critiques and loops back when needed
- Generates deliverables (chat, slides, documents)

Supports multiple LLM providers: Gemini, Ollama (local), OpenAI
"""

__version__ = "0.1.0"

from copilot.agent.workflow import ResearchCopilot, create_copilot
from copilot.llm import get_llm

__all__ = ["ResearchCopilot", "create_copilot", "get_llm", "__version__"]