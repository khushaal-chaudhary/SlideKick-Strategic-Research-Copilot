# Strategic Research Copilot - Agent Package

The core LangGraph agent that powers the Strategic Research Copilot.

## Features

- **Multi-step planning** - Decomposes complex queries into research steps
- **Multi-source retrieval** - Graph, vector, and web search
- **Self-critique loop** - Evaluates quality and loops back if needed
- **Multiple output formats** - Chat, slides, documents

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
from copilot import create_copilot

copilot = create_copilot()
response = copilot.get_response("What are Microsoft's AI strategies?")
print(response)
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LLM Provider (gemini, ollama, or openai)
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b

# Neo4j
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## CLI

```bash
copilot chat      # Interactive mode
copilot status    # Check connections
```
