---
title: SlideKick
emoji: ⚡
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# SlideKick

An AI research copilot that fans out across a knowledge graph, vector search, web search, and financial APIs in parallel, reranks and self-critiques the results until confident, then streams the answer token-by-token — or hands you a downloadable slide deck. Every answer is scored by an automated eval harness whose results are public.

**Created by [Khushaal Chaudhary](https://khushaalchaudhary.com)** | [LinkedIn](https://linkedin.com/in/khushaal-chaudhary) | [GitHub](https://github.com/khushaal-chaudhary)

**Live Demo:** [HuggingFace Spaces](https://huggingface.co/spaces/khushaal/slidekick) · **Quality Metrics:** `/metrics` on the demo · **Tech Wiki:** `/wiki` on the demo (every design decision, explained)

---

## Highlights

- **Self-correcting agent** — a Critic node scores each research pass; below threshold, it loops back with a targeted refinement (more graph, more web, or financial data) instead of answering badly.
- **Parallel retrieval fan-out** — LangGraph `Send` dispatches graph, vector, web, and financial retrieval concurrently; a cross-encoder reranks the merged evidence before analysis.
- **Public eval harness** — ragas metrics (faithfulness, answer relevancy, context precision) plus custom judges, including *critic calibration* (does the agent's self-assessed quality track an external judge?). Results are committed to the repo, served by the API, and rendered on the `/metrics` dashboard.
- **Bring your own documents** — upload a PDF or text file and query it alongside the demo corpus. User data is namespaced in the same Neo4j instance and auto-purged after 24 h.
- **Token-level streaming** — the final answer streams word-by-word over SSE while the agent's internal events (node transitions, retrievals, critic decisions) stream in parallel.
- **Runs entirely on free tiers** — Groq + Gemini + Neo4j Aura free + HF Spaces CPU + Vercel. The Tech Wiki documents every tradeoff that made this possible.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Agent Nodes Explained](#agent-nodes-explained)
5. [Evaluation](#evaluation)
6. [Project Structure](#project-structure)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Usage](#usage)
10. [API Reference](#api-reference)
11. [Output Formats](#output-formats)
12. [Adding Your Own Data](#adding-your-own-data)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)
15. [Development](#development)
16. [Tech Stack](#tech-stack)
17. [License](#license)

---

## What It Does

SlideKick takes your research question and processes it through a multi-step AI pipeline:

1. **Planner** — analyzes your question, extracts entities, and picks a retrieval strategy
2. **Retrieval fan-out** — graph, vector, web, and financial retrieval run **in parallel**
3. **Reranker** — a cross-encoder re-scores the merged evidence for relevance
4. **Analyzer** — finds patterns and generates insights from the data
5. **Critic** — scores quality and decides if more research is needed
6. **Generator** — creates the final output (chat response or slides), streamed token-by-token
7. **Responder** — formats and delivers the response

The key difference from simple RAG: SlideKick **loops back** if the quality isn't good enough. The Critic node evaluates the research and can send it back for another targeted retrieval pass.

### Example Flow

```
You: "How is Microsoft positioned against Google in AI?"

Planner    → Identified entities: Microsoft, Google, AI
           → Strategy: hybrid (graph + vector + web)
           → Query type: Strategic (will generate slides)

Retrieval  → Graph search: Found 23 Microsoft AI entities   ┐
           → Vector search: Found 12 relevant chunks        ├─ in parallel
           → Web search: Found 12 recent articles           ┘

Reranker   → Cross-encoder re-scored 47 results, kept top evidence

Analyzer   → Insight 1: Microsoft leads in enterprise AI integration
           → Insight 2: Google dominates AI research publications
           → Insight 3: Both competing heavily in cloud AI services

Critic     → Quality score: 0.72 (below 0.8 threshold)
           → Gap: Missing recent partnership data
           → Decision: Loop back for more web search

Retrieval  → Additional web search: Found 8 partnership articles

Critic     → Quality score: 0.89 (above threshold)
           → Decision: Proceed to generation

Generator  → Streaming answer tokens... / Creating PowerPoint...

Responder  → Response delivered
```

---

## Features

### LLM Provider Toggle

Switch between LLM providers from the web interface. The choice travels **per-request through agent state** (not a global), so concurrent users can use different providers safely.

| Provider | Speed | Rate Limits | Cost | Best For |
|----------|-------|-------------|------|----------|
| **Groq** | Fast | Yes (see below) | Free tier | Production demos |
| **Ollama** | Slower | None | Free | Development, unlimited use |

**Groq Rate Limits (Free Tier):**
- 30 requests per minute
- 14,400 requests per day
- 6,000 tokens per minute (varies by model)

When Groq hits a rate limit, SlideKick shows which limit was hit, how long to wait, and suggests switching to Ollama.

### Data Sources

**Knowledge Graph (Neo4j)**
- Pre-loaded with Microsoft Shareholder Letters 2020–2024, modeled with schema.org types
- Entities, relationships, and embedded document chunks (hybrid graph + vector retrieval)
- Parameterized Cypher throughout, plus defense-in-depth input caps

**Web Search (Tavily)**
- Real-time web search for current information with AI-powered summarization

**Financial API (Alpha Vantage)**
- Stock quotes, fundamentals (P/E, EPS, margins), income statements, news sentiment
- Free tier: 25 requests per day

**Your Documents (BYOD)**
- Upload PDF/TXT from the UI; entities are extracted into the same schema.org graph under an isolated namespace — see [Adding Your Own Data](#adding-your-own-data)

### Cross-Encoder Reranking

After the parallel fan-out, merged results are re-scored by `cross-encoder/ms-marco-MiniLM-L-6-v2` (runs on CPU, free). Rerank scores are emitted in the SSE stream so you can watch evidence being re-ordered live in the log viewer.

### Real-time Streaming

Two things stream simultaneously over one SSE connection:
- **Agent events** — which node is active, what was retrieved, quality scores, critic decisions
- **Answer tokens** — the final response renders word-by-word as the Generator produces it

### Evaluation Dashboard

The `/metrics` page renders the latest eval run: per-metric scores, run-over-run trends, and per-query drill-down. See [Evaluation](#evaluation).

### Slide Generation

When slides are generated:
1. First attempts Google Slides API (creates shareable link)
2. Falls back to python-pptx (downloadable .pptx)

### Tech Wiki

The `/wiki` page in the app answers ~25 questions about the design: why an agent instead of plain RAG, why schema.org, how BYOD namespacing works, what breaks at scale, and every free-tier tradeoff.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              WEB UI (Next.js 15, Vercel)                 │
│                                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ ┌───────┐  │
│  │ Query Input │ │  Log Viewer │ │  Response   │ │Metrics │ │ Wiki  │  │
│  │  + upload   │ │ (SSE stream)│ │(token strm) │ │ (evals)│ │       │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ └───────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP POST + SSE
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API (FastAPI + SSE, HF Spaces)                    │
│                                                                          │
│  POST /api/query               → Submit research question               │
│  GET  /api/stream/:id          → SSE: agent events + answer tokens      │
│  POST /api/documents/upload    → BYOD ingestion (SSE progress)          │
│  GET  /api/evals/latest        → Latest eval results                    │
│  GET  /api/download/:file      → Download generated presentations       │
│                                                                          │
│  SQLite session snapshots (survive Space restarts)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LANGGRAPH AGENT                                 │
│                                                                          │
│  ┌──────────┐        parallel fan-out (Send)                            │
│  │ Planner  │ ─▶ ┌───────────┬───────────┬──────────┬───────────┐      │
│  └──────────┘    │   Graph   │  Vector   │   Web    │ Financial │      │
│                  │ retrieval │ retrieval │retrieval │ retrieval │      │
│                  └─────┬─────┴─────┬─────┴────┬─────┴─────┬─────┘      │
│                        └───────────┴────┬─────┴───────────┘            │
│                                         ▼                               │
│                                  ┌────────────┐                         │
│                                  │  Reranker  │  cross-encoder          │
│                                  └─────┬──────┘                         │
│                                        ▼                                │
│                  ┌──────────┐    ┌──────────┐                           │
│              ┌── │  Critic  │ ◀─ │ Analyzer │                           │
│              │   └────┬─────┘    └──────────┘                           │
│   loop back  │        │ quality ≥ threshold                             │
│   (refine)   │        ▼                                                 │
│              │  ┌───────────┐    ┌───────────┐                          │
│              └▶ │ Generator │ ─▶ │ Responder │                          │
│    (to fan-out) └───────────┘    └───────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
                    │              │              │
                    ▼              ▼              ▼
             ┌───────────┐  ┌───────────┐  ┌───────────┐
             │   Neo4j   │  │  Tavily   │  │   Alpha   │
             │Graph+Vec  │  │  Search   │  │  Vantage  │
             └───────────┘  └───────────┘  └───────────┘
```

---

## Agent Nodes Explained

### 1. Planner

**File:** `packages/agent/src/copilot/agent/nodes/planner.py`

- Classifies query type (factual, comparative, strategic, financial, exploratory)
- Extracts entities of interest and stock symbols
- Chooses retrieval strategy and output format

**Retrieval Strategies:**
| Strategy | When Used | Description |
|----------|-----------|-------------|
| `graph_only` | Simple factual queries | Only query Neo4j |
| `hybrid` | Most queries | Graph + vector search |
| `graph_then_web` | Current events | Graph first, web if insufficient |
| `web_only` | News, recent events | Skip graph, search web |
| `financial_first` | Stock/company metrics | Start with Alpha Vantage API |

### 2. Retrieval Fan-out

**Files:** `packages/agent/src/copilot/agent/nodes/retrieval/{graph,vector,web,financial}.py`

The planner's strategy is dispatched via LangGraph `Send` — each selected source runs as its **own node, concurrently**. Result lists in state use `operator.add` reducers, so parallel branches merge automatically. When the Critic loops back, only the single source it needs is re-dispatched.

| Node | Source | Data Retrieved |
|------|--------|----------------|
| `graph_retrieval` | Neo4j Cypher | Entities, relationships (namespace-filtered for BYOD) |
| `vector_retrieval` | Neo4j vector indexes | Similar chunks from demo corpus + user docs |
| `web_retrieval` | Tavily | Current articles, AI-summarized results |
| `financial_retrieval` | Alpha Vantage | Quotes, fundamentals, financials, news |

### 3. Reranker

**File:** `packages/agent/src/copilot/agent/nodes/retrieval/reranker.py`

Re-scores all merged retrieval results against the query with `cross-encoder/ms-marco-MiniLM-L-6-v2`. Cheap (CPU-only), model-free-tier-independent, and measurably improves the evidence the Analyzer sees. Scores are surfaced in SSE events.

### 4. Analyzer

**File:** `packages/agent/src/copilot/agent/nodes/analyzer.py`

Synthesizes reranked data into structured insights with confidence scores. Categories: `strategic_theme`, `competitive_gap`, `investment_pattern`, `market_trend`, `risk_factor`.

### 5. Critic

**File:** `packages/agent/src/copilot/agent/nodes/critic.py`

Scores research quality (0.0–1.0, threshold 0.8), identifies gaps, and decides whether to loop back with a targeted refinement:

| Type | When Triggered | Action |
|------|----------------|--------|
| `web_search` | Missing current data | Re-dispatch web retrieval |
| `more_graph` | Need deeper entity data | Re-dispatch graph retrieval |
| `financial_data` | Missing company metrics | Re-dispatch financial retrieval |
| `none` | Quality sufficient | Proceed to Generator |

The eval harness checks whether these self-scores actually correlate with an external judge — see [Evaluation](#evaluation).

### 6. Generator

**File:** `packages/agent/src/copilot/agent/nodes/generator.py`

Creates the final output. Chat responses are **streamed token-by-token** to the client via LangGraph's `messages` stream mode. Slides go through Google Slides API or python-pptx.

### 7. Responder

**File:** `packages/agent/src/copilot/agent/nodes/responder.py`

Formats the final response and attaches metadata (quality score, sources used, iterations).

---

## Evaluation

Answer quality is measured, not asserted. The harness lives in `evals/` and its output is public.

**Golden dataset** — `evals/golden_dataset.jsonl`: curated queries over the Microsoft corpus with expected facts and entities.

**Metrics:**

| Metric | Source | What it measures |
|--------|--------|------------------|
| Faithfulness | ragas | Is the answer grounded in retrieved context? |
| Answer relevancy | ragas | Does the answer address the question? |
| Context precision | ragas | Is the retrieved evidence actually relevant? |
| Fact recall | custom judge | Are the expected facts present in the answer? |
| **Critic calibration** | custom | Does the agent's own quality score correlate with an external judge's score? |

Critic calibration is the distinctive one: a self-reflective agent whose confidence doesn't track reality is worse than no critic at all.

**Judge model** — a different model family (Gemini flash by default, configurable via `EVAL_JUDGE_PROVIDER`) judges the answers, avoiding same-family self-preference bias.

**How it runs:**
- Locally: `python evals/run_evals.py [--subset n] [--start i] [--sleep s]` (sleeps between queries to respect free-tier quotas)
- CI: `.github/workflows/evals.yml` — weekly cron + manual dispatch; commits updated results
- Results: `evals/results/YYYY-MM-DD.json` + `latest.json`, served at `GET /api/evals/latest`, rendered on the **/metrics** dashboard with run-over-run trends and per-query drill-down

---

## Project Structure

```
slidekick/
│
├── web/                                    # Next.js 15 Frontend (Vercel)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                    # Main research page
│   │   │   ├── metrics/                    # Eval dashboard
│   │   │   └── wiki/                       # Tech decisions wiki
│   │   ├── components/
│   │   │   ├── query-input.tsx             # Search input with LLM toggle
│   │   │   ├── document-upload.tsx         # BYOD dropzone + progress
│   │   │   ├── log-viewer.tsx              # Real-time agent logs
│   │   │   ├── response-viewer.tsx         # Streaming response + download
│   │   │   ├── eval-dashboard.tsx          # Metrics charts (recharts)
│   │   │   ├── wiki-content.tsx            # Searchable Q&A wiki
│   │   │   └── ui/                         # shadcn/ui components
│   │   ├── hooks/
│   │   │   ├── use-research.ts             # SSE hook (events + tokens)
│   │   │   └── use-ingestion.ts            # SSE hook for BYOD progress
│   │   └── lib/constants.ts                # API URLs, config
│   └── package.json
│
├── api/                                    # FastAPI Backend (HF Spaces)
│   ├── main.py                             # Endpoints, SSE, token streaming
│   ├── documents.py                        # BYOD upload/ingestion router
│   ├── sessions.py                         # SQLite session persistence
│   ├── schemas.py                          # Pydantic models
│   ├── config.py                           # API settings
│   ├── tests/                              # API test suite
│   └── Dockerfile                          # HF Spaces deployment
│
├── packages/
│   ├── agent/                              # LangGraph Agent Package
│   │   ├── src/copilot/
│   │   │   ├── agent/
│   │   │   │   ├── nodes/
│   │   │   │   │   ├── planner.py
│   │   │   │   │   ├── retrieval/          # Parallel fan-out nodes
│   │   │   │   │   │   ├── graph.py
│   │   │   │   │   │   ├── vector.py
│   │   │   │   │   │   ├── web.py
│   │   │   │   │   │   ├── financial.py
│   │   │   │   │   │   └── reranker.py     # Cross-encoder rerank
│   │   │   │   │   ├── analyzer.py
│   │   │   │   │   ├── critic.py
│   │   │   │   │   ├── generator.py
│   │   │   │   │   └── responder.py
│   │   │   │   ├── state.py                # ResearchState (+ reducers)
│   │   │   │   └── workflow.py             # LangGraph wiring (Send fan-out)
│   │   │   ├── ingestion/                  # BYOD pipeline
│   │   │   │   ├── pipeline.py             # Orchestration + progress events
│   │   │   │   ├── parser.py               # PDF/TXT parsing
│   │   │   │   ├── chunker.py
│   │   │   │   ├── extractor.py            # schema.org entity extraction
│   │   │   │   └── writer.py               # Namespaced Neo4j MERGE
│   │   │   ├── graph/connection.py         # Neo4j connection
│   │   │   ├── llm.py                      # LLM factory (per-request provider)
│   │   │   └── interfaces/cli.py           # Command line interface
│   │   └── tests/                          # Agent test suite (mocked LLM)
│   │
│   ├── mcp-financial/                      # Alpha Vantage MCP Server
│   └── google-slides-mcp/                  # Google Slides MCP Server
│
├── evals/                                  # Eval harness
│   ├── golden_dataset.jsonl
│   ├── run_evals.py
│   ├── judges.py
│   └── results/                            # Committed run outputs
│
├── .github/workflows/
│   ├── ci.yml                              # ruff + pytest + next build
│   └── evals.yml                           # Weekly eval runs
│
├── data/microsoft-letters/                 # Demo corpus (2020–2024)
└── graph_ingestion_schemaorg.ipynb         # Demo-corpus ingestion notebook
```

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Neo4j database (local or Neo4j Aura free tier)
- Ollama (for local LLM) or Groq API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/khushaal-chaudhary/slidekick.git
cd slidekick
```

### Step 2: Install the Agent Package

```bash
cd packages/agent
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install the package
pip install -e ".[dev]"
```

### Step 3: Install the Web Frontend

```bash
cd ../../web
npm install
```

### Step 4: Install the API Dependencies

```bash
cd ../api
pip install -r requirements.txt
```

### Step 5: Set Up Ollama (Optional, for local LLM)

```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull qwen2.5:7b
```

### Step 6: Set Up Neo4j

**Option A: Neo4j Aura (Cloud, Recommended for Quick Start)**
1. Go to [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/)
2. Create a free instance
3. Save the connection URI, username, and password

**Option B: Local Neo4j**
1. Download Neo4j Desktop from [neo4j.com/download](https://neo4j.com/download/)
2. Create a new database
3. Start the database and note the bolt URI (usually `bolt://localhost:7687`)

---

## Configuration

### Environment Variables

Create a `.env` file in `packages/agent/`:

```bash
cp packages/agent/.env.example packages/agent/.env
```

Edit the file with your values:

```bash
# =============================================================================
# NEO4J - Knowledge Graph Database (Required)
# =============================================================================
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # Your Neo4j connection URI
NEO4J_USERNAME=neo4j                            # Usually "neo4j"
NEO4J_PASSWORD=your_password                    # Your database password

# =============================================================================
# LLM PROVIDER - Choose your AI model (Required)
# =============================================================================
# Options: ollama, groq, gemini, openai
LLM_PROVIDER=groq

# Model name depends on provider:
# - groq: llama-3.3-70b-versatile, mixtral-8x7b-32768
# - ollama: qwen2.5:7b, llama3.2:3b, mistral:7b
# - gemini: gemini-1.5-flash, gemini-1.5-pro
# - openai: gpt-4o-mini, gpt-4o
LLM_MODEL=llama-3.3-70b-versatile

# Temperature (0.0 = deterministic, 1.0 = creative)
LLM_TEMPERATURE=0.0

# =============================================================================
# GROQ - Fast Cloud LLM (Required if LLM_PROVIDER=groq)
# =============================================================================
# Get free key at: https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# =============================================================================
# GEMINI - Used for BYOD extraction and eval judging (Optional)
# =============================================================================
GOOGLE_API_KEY=your_gemini_key

# =============================================================================
# OLLAMA - Local LLM (Required if LLM_PROVIDER=ollama)
# =============================================================================
OLLAMA_BASE_URL=http://localhost:11434

# =============================================================================
# FALLBACK LLM - Used when primary provider fails
# =============================================================================
# Options: ollama, none
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=qwen2.5:7b

# =============================================================================
# TAVILY - Web Search (Optional but recommended)
# =============================================================================
# Get free key at: https://tavily.com
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx

# =============================================================================
# ALPHA VANTAGE - Financial Data (Optional)
# =============================================================================
# Get free key at: https://www.alphavantage.co/support/#api-key
# Free tier: 25 requests per day
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# =============================================================================
# GOOGLE SLIDES - Presentation Generation (Optional)
# =============================================================================
# Service account credentials JSON path
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# =============================================================================
# LANGSMITH - Debugging & Tracing (Optional)
# =============================================================================
# Get key at: https://smith.langchain.com
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_xxxxxxxxxxxxxxxxxxxx
LANGCHAIN_PROJECT=slidekick

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================
# Quality threshold for critic (0.0-1.0)
QUALITY_THRESHOLD=0.8

# Maximum research iterations before stopping
MAX_ITERATIONS=3
```

### API Configuration

For the API server, create `api/.env`:

```bash
# API Settings
API_TITLE=SlideKick API
API_VERSION=1.0.0
DEBUG=false

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Agent settings
MAX_ITERATIONS=3
```

---

## Usage

### Running Locally

**Terminal 1: Start the API**
```bash
cd api
python main.py
# API runs at http://localhost:7860
```

**Terminal 2: Start the Web UI**
```bash
cd web
npm run dev
# Web UI runs at http://localhost:3000
```

**Terminal 3 (Optional): Start Ollama**
```bash
ollama serve
# Ollama API runs at http://localhost:11434
```

### Using the Web Interface

1. **Open the app** at http://localhost:3000
2. **Select LLM provider** using the toggle (Groq: faster with rate limits; Ollama: slower, unlimited)
3. **Optionally upload a document** to query your own data
4. **Enter your question** and watch the agent's progress in the log viewer
5. **Read the answer as it streams** in the response panel
6. **Download slides** if a presentation was generated
7. **Explore `/metrics`** for eval results and **`/wiki`** for design decisions

### Using the CLI

```bash
cd packages/agent
source venv/bin/activate

# Interactive chat mode
copilot chat

# Single query
copilot query "What is Microsoft's AI strategy?"
```

### Example Queries

**Strategic Questions (generates slides):**
- "How should Microsoft respond to Google's AI advances?"
- "What competitive advantages does Azure have over AWS?"
- "Analyze Microsoft's acquisition strategy 2020-2024"

**Comparative Questions (generates slides):**
- "Compare Microsoft and Apple's approach to AI"
- "How does GitHub Copilot compare to Amazon CodeWhisperer?"

**Financial Questions:**
- "What is Microsoft's current P/E ratio?"
- "Compare MSFT and GOOGL revenue growth"

**Factual Questions:**
- "When did Microsoft invest in OpenAI?"
- "What products did Microsoft launch in 2023?"

**Exploratory Questions:**
- "What are the key themes in Microsoft's 2024 shareholder letter?"
- "Summarize Microsoft's cloud strategy"

---

## API Reference

### Base URL

- Local: `http://localhost:7860`
- Production: `https://khushaal-slidekick.hf.space`

### Endpoints

#### POST /api/query

Submit a research query.

**Request:**
```json
{
  "query": "How has Microsoft's AI strategy evolved?",
  "llm_provider": "groq",
  "max_iterations": 3,
  "workspace_id": "optional-byod-namespace-uuid"
}
```

**Response:**
```json
{
  "session_id": "abc123-def456",
  "query": "How has Microsoft's AI strategy evolved?",
  "status": "pending",
  "stream_url": "/api/stream/abc123-def456",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/stream/{session_id}

Stream real-time events via Server-Sent Events (SSE).

**Event Types:**

| Event | Description |
|-------|-------------|
| `start` | Processing started |
| `node_start` | Agent node started |
| `node_complete` | Agent node finished |
| `retrieval` | Data retrieved from source (includes rerank scores) |
| `insight` | Analysis insight generated |
| `decision` | Critic made a decision |
| `progress` | Iteration progress update |
| `token` | A token of the final answer (streamed as generated) |
| `final_response` | Final response ready |
| `complete` | All processing done |
| `error` | Error occurred |

**Example Token Event:**
```json
{
  "type": "token",
  "session_id": "abc123",
  "content": " cloud",
  "timestamp": "2024-01-15T10:30:12Z"
}
```

**Error Event (Rate Limit):**
```json
{
  "type": "error",
  "session_id": "abc123",
  "error": "Groq Tokens per minute limit reached",
  "error_type": "rate_limit",
  "rate_limit": {
    "limit_type": "TPM",
    "limit_type_friendly": "Tokens per minute limit",
    "retry_after": 45,
    "retry_after_friendly": "45 seconds",
    "suggestion": "Try again later or switch to Ollama"
  }
}
```

#### POST /api/documents/upload

Upload a document for BYOD ingestion (multipart form: `file` + `workspace_id`). Limits: ~10 MB, PDF/TXT. Returns a session whose progress streams from `GET /api/documents/stream/{session_id}` with events: `parsing`, `chunked`, `extracting`, `embedding`, `graph_write`, `ingest_complete`.

#### GET /api/documents/{workspace_id}

List documents ingested into a workspace.

#### DELETE /api/documents/{workspace_id}

Delete a workspace and all its namespaced graph data. (Workspaces are also auto-purged after 24 hours.)

#### GET /api/evals/latest

Latest eval run results (the JSON behind the `/metrics` dashboard).

#### GET /api/session/{session_id}

Get the current state of a session. Sessions are snapshotted to SQLite, so completed sessions survive server restarts; sessions interrupted by a restart are reported as errors rather than hanging.

#### GET /api/download/{filename}

Download a generated PowerPoint presentation (binary .pptx; files expire after 1 hour).

#### GET /api/debug/neo4j

Debug endpoint to check Neo4j connection (labels, relationship types, node counts).

#### GET /health

Health check endpoint.

---

## Output Formats

### Chat Response

Returned for factual, financial, and exploratory queries. Markdown, streamed token-by-token.

### Slides (PowerPoint)

Returned for strategic and comparative queries.

**Slide Structure:**
1. **Title Slide** — query summary and date
2. **Executive Summary** — key findings overview
3. **Content Slides** (3–5) — detailed analysis with bullets
4. **Conclusion** — recommendations or summary

**Generation Priority:**
1. Google Slides API (creates shareable link)
2. python-pptx fallback (creates downloadable file)
3. Text-based slides (if both fail)

---

## Adding Your Own Data

### Option A: Upload from the UI (BYOD)

The easiest path — no notebooks, no credentials:

1. Drop a PDF or text file into the upload zone on the main page
2. Watch live ingestion progress (parsing → chunking → entity extraction → embedding → graph write)
3. Ask questions — retrieval automatically searches your documents alongside the demo corpus

**How it works under the hood:**
- Your browser gets a `workspace_id` (UUID in localStorage) that namespaces everything you upload
- Chunks are extracted into schema.org entities (Gemini flash, Groq fallback) and written with `:UserDoc`/`:UserChunk` labels + a `namespace` property — the demo corpus is physically untouched
- A second vector index (`user_doc_embeddings`) serves your chunks; graph queries filter by namespace
- Workspaces are purged after 24 hours to stay within the Aura free-tier node budget

**Limits:** ~10 MB per file, PDF/TXT, capped chunk count per upload.

### Option B: Bulk Ingestion (Notebook)

For replacing/extending the demo corpus itself, use `graph_ingestion_schemaorg.ipynb`:

1. Place documents in `data/your-folder/`
2. Update `DOCUMENTS_PATH` in the notebook
3. Run all cells: load → chunk → LLM entity extraction → relationships → Neo4j
4. Verify with `GET /api/debug/neo4j`

### Schema

The graph uses **schema.org** types (`Organization`, `Product`, `Person`, etc.) plus:

**Node Labels:** `Document`, `Chunk` (embedded), `UserDoc`/`UserChunk` (BYOD)

**Relationships:** `RELATED_TO`, `MENTIONS`, `PART_OF`, and schema.org-derived relations

---

## Deployment

### Frontend (Vercel)

1. Push to GitHub
2. Import the repo at [vercel.com](https://vercel.com), set root directory to `web`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-hf-space.hf.space`
4. Deploy

### Backend (HuggingFace Spaces)

1. Create a Docker-SDK Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Push the repo to the Space (the root `Dockerfile`/frontmatter target `app_port: 7860`)
3. In Space Settings → Repository Secrets, add:
   - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
   - `GROQ_API_KEY`, `GOOGLE_API_KEY`
   - `TAVILY_API_KEY`, `ALPHA_VANTAGE_API_KEY`
4. Verify via the Space logs and the `/health` endpoint

### CI

`.github/workflows/ci.yml` runs ruff, the Python test suites (agent + API), and `next build` on every push. `.github/workflows/evals.yml` runs the eval suite weekly and commits refreshed results.

---

## Troubleshooting

### Common Issues

#### "Agent not available"

**Cause:** The agent package isn't properly installed or importable.

**Fix:**
```bash
cd packages/agent
pip install -e ".[dev]"
```

#### "Neo4j connection failed"

**Fix:**
1. Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env
2. Check `GET /api/debug/neo4j`
3. For Aura: ensure the URI starts with `neo4j+s://`; some Aura instances use the instance ID as both username and database name

#### "Groq rate limit reached"

**Fix:** switch to Ollama in the UI, or wait for the time shown in the error message (the API surfaces the exact limit and retry time).

#### "No results from knowledge graph"

**Fix:**
1. Check graph contents: `GET /api/debug/neo4j`
2. Run the ingestion notebook to populate data
3. Verify entity names match your documents

#### "Slides generation failed"

**Fix:** python-pptx fallback should work automatically; for Google Slides verify the service account.

#### "Ollama connection refused"

**Fix:**
```bash
ollama serve
# Then verify:
curl http://localhost:11434/api/tags
```

#### "Session was interrupted by a server restart"

The API restarted (HF Spaces free tier sleeps) mid-query. Completed sessions are recoverable from SQLite; in-flight ones are reported as errors — just re-run the query.

### Debug Mode

```bash
# In .env
DEBUG=true
LANGCHAIN_TRACING_V2=true
```

View traces at [smith.langchain.com](https://smith.langchain.com)

---

## Development

### Running Tests

```bash
# Agent package (LLM calls mocked — runs offline)
cd packages/agent
pytest tests/

# API (FastAPI TestClient, agent mocked)
cd ../../api
pytest tests/
```

Coverage includes workflow routing, state reducers, node behavior with a fake LLM, BYOD chunking/writing, SSE endpoints, and SQLite session persistence.

### Running Evals

```bash
python evals/run_evals.py --subset 5   # quick sanity pass
python evals/run_evals.py              # full golden dataset
```

Results land in `evals/results/` and are picked up by `/api/evals/latest` and the `/metrics` page.

### Code Structure

**Adding a new agent node:**

1. Create `packages/agent/src/copilot/agent/nodes/your_node.py`
2. Define the node function that takes and returns `ResearchState`
3. Add to workflow in `workflow.py` and wire the edges

**Adding a new retrieval source:**

1. Add a node in `nodes/retrieval/your_source.py`
2. Add a result field with an `operator.add` reducer in `state.py`
3. Register it in the fan-out dispatch in `workflow.py`

### Local Development with Hot Reload

```bash
# API
cd api
python main.py

# Web
cd web
npm run dev
```

---

## Tech Stack

| Technology | Purpose | Documentation |
|------------|---------|---------------|
| **LangGraph** | Agent orchestration: conditional loops + `Send` fan-out | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) |
| **LangChain** | LLM integration and prompts | [python.langchain.com](https://python.langchain.com/) |
| **Neo4j** | Knowledge graph + vector indexes | [neo4j.com/docs](https://neo4j.com/docs/) |
| **ragas** | RAG evaluation metrics | [docs.ragas.io](https://docs.ragas.io/) |
| **sentence-transformers** | Cross-encoder reranking | [sbert.net](https://www.sbert.net/) |
| **Next.js 15** | React framework with App Router | [nextjs.org/docs](https://nextjs.org/docs) |
| **FastAPI** | Python API framework | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) |
| **SSE-Starlette** | Server-Sent Events for streaming | [github.com/sysid/sse-starlette](https://github.com/sysid/sse-starlette) |
| **Groq** | Fast LLM inference | [console.groq.com/docs](https://console.groq.com/docs) |
| **Gemini** | BYOD extraction + eval judging | [ai.google.dev](https://ai.google.dev/) |
| **Ollama** | Local LLM server | [ollama.ai](https://ollama.ai/) |
| **Tavily** | AI-powered web search | [tavily.com](https://tavily.com/) |
| **Alpha Vantage** | Financial data API | [alphavantage.co/documentation](https://www.alphavantage.co/documentation/) |
| **python-pptx** | PowerPoint generation | [python-pptx.readthedocs.io](https://python-pptx.readthedocs.io/) |
| **recharts** | Eval dashboard charts | [recharts.org](https://recharts.org/) |
| **shadcn/ui + Tailwind CSS** | UI components and styling | [ui.shadcn.com](https://ui.shadcn.com/) |

---

## License

MIT License - Use it however you want.

---

## Acknowledgments

- Microsoft Shareholder Letters used for demo knowledge graph
- LangChain team for LangGraph
- Anthropic, Groq, Google, and Ollama for LLM access
