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

An AI research copilot that searches knowledge graphs, fetches live data, self-critiques until confident, and delivers insights as chat responses or downloadable presentations.

**Created by [Khushaal Chaudhary](https://khushaalchaudhary.com)** | [LinkedIn](https://linkedin.com/in/khushaal-chaudhary) | [GitHub](https://github.com/khushaal-chaudhary)

**Live Demo:** [HuggingFace Spaces](https://huggingface.co/spaces/khushaal/slidekick)

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Agent Nodes Explained](#agent-nodes-explained)
5. [Project Structure](#project-structure)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [API Reference](#api-reference)
10. [Output Formats](#output-formats)
11. [Adding Your Own Data](#adding-your-own-data)
12. [Deployment](#deployment)
13. [Troubleshooting](#troubleshooting)
14. [Development](#development)
15. [Tech Stack](#tech-stack)
16. [License](#license)

---

## What It Does

SlideKick takes your research question and processes it through a multi-step AI pipeline:

1. **Planner** - Analyzes your question and creates a research plan
2. **Retriever** - Gathers data from knowledge graph, web search, and financial APIs
3. **Analyzer** - Finds patterns and generates insights from the data
4. **Critic** - Evaluates quality and decides if more research is needed
5. **Generator** - Creates the final output (chat response or slides)
6. **Responder** - Formats and delivers the response

The key difference from simple RAG: SlideKick **loops back** if the quality isn't good enough. The Critic node evaluates the research and can send it back to the Retriever for more data.

### Example Flow

```
You: "How is Microsoft positioned against Google in AI?"

Planner    → Identified entities: Microsoft, Google, AI
           → Strategy: Graph first, then web search
           → Query type: Strategic (will generate slides)

Retriever  → Graph search: Found 23 Microsoft AI entities
           → Graph search: Found 8 Google AI entities
           → Web search: Found 12 recent articles

Analyzer   → Insight 1: Microsoft leads in enterprise AI integration
           → Insight 2: Google dominates AI research publications
           → Insight 3: Both competing heavily in cloud AI services

Critic     → Quality score: 0.72 (below 0.8 threshold)
           → Gap: Missing recent partnership data
           → Decision: Loop back for more web search

Retriever  → Additional web search: Found 8 partnership articles

Critic     → Quality score: 0.89 (above threshold)
           → Decision: Proceed to generation

Generator  → Creating PowerPoint presentation...
           → 6 slides generated

Responder  → Presentation ready for download
```

---

## Features

### LLM Provider Toggle

Switch between LLM providers from the web interface:

| Provider | Speed | Rate Limits | Cost | Best For |
|----------|-------|-------------|------|----------|
| **Groq** | Fast | Yes (see below) | Free tier | Production demos |
| **Ollama** | Slower | None | Free | Development, unlimited use |

**Groq Rate Limits (Free Tier):**
- 30 requests per minute
- 14,400 requests per day
- 6,000 tokens per minute (varies by model)

When Groq hits a rate limit, SlideKick shows:
- Which limit was hit (tokens/minute, requests/day, etc.)
- How long to wait before retrying
- Suggestion to switch to Ollama

### Data Sources

**Knowledge Graph (Neo4j)**
- Pre-loaded with Microsoft Shareholder Letters 2020-2024
- Contains entities, relationships, and document chunks
- Supports Cypher queries for structured data retrieval

**Web Search (Tavily)**
- Real-time web search for current information
- AI-powered result summarization
- Used when graph data is insufficient or outdated

**Financial API (Alpha Vantage)**
- Stock quotes and price data
- Company fundamentals (P/E, EPS, margins)
- Income statements
- News sentiment
- Free tier: 25 requests per day

### Output Formats

SlideKick automatically chooses the output format based on your question:

| Query Type | Example | Output |
|------------|---------|--------|
| **Strategic** | "How should we respond to competitor X?" | Slides |
| **Comparative** | "Compare Microsoft vs Google AI strategy" | Slides |
| **Financial** | "What is Apple's P/E ratio?" | Chat |
| **Factual** | "When did Microsoft acquire OpenAI stake?" | Chat |
| **Exploratory** | "What are the key themes in the 2024 letter?" | Chat |

### Slide Generation

When slides are generated:
1. First attempts Google Slides API (creates shareable link)
2. If Google Slides unavailable, falls back to python-pptx
3. PowerPoint file is available for download

Slide content includes:
- Title slide with query summary
- 4-6 content slides with key findings
- Each bullet point: 20-35 words with "Key Point: Explanation" format

### Real-time Streaming

The web interface shows live progress:
- Which node is currently active
- What data is being retrieved
- Quality scores and decisions
- Time elapsed for each step

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              WEB UI                                      │
│                           (Next.js 15)                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Query Input  │  │  Log Viewer  │  │   Response   │                   │
│  │              │  │  (SSE stream)│  │    Viewer    │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP POST + SSE
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               API                                        │
│                         (FastAPI + SSE)                                  │
│                                                                          │
│  POST /api/query     → Submit research question                         │
│  GET  /api/stream/:id → SSE stream of agent events                      │
│  GET  /api/download/:file → Download generated presentations            │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Runs agent in thread
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LANGGRAPH AGENT                                 │
│                                                                          │
│   ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐        │
│   │ Planner  │ ─▶ │ Retriever │ ─▶ │ Analyzer │ ─▶ │  Critic  │        │
│   └──────────┘    └───────────┘    └──────────┘    └──────────┘        │
│                          ▲                               │              │
│                          │                               │              │
│                          │    ┌──────────────────────────┘              │
│                          │    │                                         │
│                          │    ▼                                         │
│                     ┌────────────┐                                      │
│                     │ Quality OK? │                                      │
│                     │  YES │ NO   │                                      │
│                     └──────┴──────┘                                      │
│                          │                                               │
│                          │ YES                                           │
│                          ▼                                               │
│                   ┌───────────┐    ┌───────────┐                        │
│                   │ Generator │ ─▶ │ Responder │                        │
│                   └───────────┘    └───────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
                    │              │              │
                    ▼              ▼              ▼
             ┌───────────┐  ┌───────────┐  ┌───────────┐
             │   Neo4j   │  │  Tavily   │  │   Alpha   │
             │   Graph   │  │  Search   │  │  Vantage  │
             └───────────┘  └───────────┘  └───────────┘
```

---

## Agent Nodes Explained

### 1. Planner

**File:** `packages/agent/src/copilot/agent/nodes/planner.py`

**What it does:**
- Analyzes the user's question
- Classifies query type (factual, comparative, strategic, financial, exploratory)
- Extracts entities of interest (company names, products, people)
- Extracts stock symbols for financial queries (MSFT, AAPL, etc.)
- Chooses retrieval strategy
- Determines output format

**Retrieval Strategies:**
| Strategy | When Used | Description |
|----------|-----------|-------------|
| `graph_only` | Simple factual queries | Only query Neo4j |
| `hybrid` | Most queries | Graph + vector search |
| `graph_then_web` | Current events | Graph first, web if insufficient |
| `web_only` | News, recent events | Skip graph, search web |
| `financial_first` | Stock/company metrics | Start with Alpha Vantage API |

### 2. Retriever

**File:** `packages/agent/src/copilot/agent/nodes/retriever.py`

**What it does:**
- Executes the retrieval strategy from the Planner
- Queries Neo4j knowledge graph for entities and relationships
- Performs web search via Tavily API
- Fetches financial data from Alpha Vantage
- Aggregates results from all sources

**Data Sources:**
| Source | Data Retrieved |
|--------|----------------|
| Neo4j Graph | Entities, relationships, document chunks |
| Tavily Web | Current articles, news, AI-summarized results |
| Alpha Vantage | Stock quotes, fundamentals, financials, news |

### 3. Analyzer

**File:** `packages/agent/src/copilot/agent/nodes/analyzer.py`

**What it does:**
- Synthesizes retrieved data into coherent insights
- Identifies patterns and themes
- Generates structured insights with confidence scores
- Creates a synthesis narrative

**Insight Categories:**
- `strategic_theme` - High-level strategic direction
- `competitive_gap` - Opportunity vs competitors
- `investment_pattern` - Financial/investment focus
- `market_trend` - Industry trend
- `risk_factor` - Potential risk or challenge

### 4. Critic

**File:** `packages/agent/src/copilot/agent/nodes/critic.py`

**What it does:**
- Evaluates the quality of current research
- Assigns a quality score (0.0 to 1.0)
- Identifies gaps in the analysis
- Decides whether to loop back for more data
- Suggests refinement type if needed

**Quality Threshold:** 0.8 (configurable)

**Refinement Types:**
| Type | When Triggered | Action |
|------|----------------|--------|
| `web_search` | Missing current data | Search web for recent info |
| `more_graph` | Need deeper entity data | Broader graph queries |
| `financial_data` | Missing company metrics | Fetch from Alpha Vantage |
| `none` | Quality sufficient | Proceed to Generator |

### 5. Generator

**File:** `packages/agent/src/copilot/agent/nodes/generator.py`

**What it does:**
- Creates the final output based on output format
- For chat: Generates markdown response
- For slides: Creates presentation content, calls Google Slides API or python-pptx
- Structures content appropriately for the format

### 6. Responder

**File:** `packages/agent/src/copilot/agent/nodes/responder.py`

**What it does:**
- Formats the final response for the user
- Adds metadata (quality score, sources used, iterations)
- Prepares the response for streaming back to the frontend

---

## Project Structure

```
slidekick/
│
├── web/                                    # Next.js 15 Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                    # Main page
│   │   │   └── layout.tsx                  # Root layout
│   │   ├── components/
│   │   │   ├── query-input.tsx             # Search input with LLM toggle
│   │   │   ├── log-viewer.tsx              # Real-time agent logs
│   │   │   ├── response-viewer.tsx         # Response display + download
│   │   │   ├── error-banner.tsx            # Rate limit error display
│   │   │   ├── header.tsx                  # Navigation header
│   │   │   ├── hero.tsx                    # Landing hero section
│   │   │   ├── tech-stack.tsx              # Technology showcase
│   │   │   └── ui/                         # shadcn/ui components
│   │   ├── hooks/
│   │   │   └── use-research.ts             # SSE hook for streaming
│   │   └── lib/
│   │       └── constants.ts                # API URLs, config
│   ├── package.json
│   └── next.config.ts
│
├── api/                                    # FastAPI Backend (HF Spaces)
│   ├── main.py                             # API endpoints, SSE streaming
│   ├── schemas.py                          # Pydantic models
│   ├── config.py                           # API settings
│   ├── Dockerfile                          # HF Spaces deployment
│   └── requirements.txt                    # Python dependencies
│
├── packages/
│   │
│   ├── agent/                              # LangGraph Agent Package
│   │   ├── src/copilot/
│   │   │   ├── agent/
│   │   │   │   ├── nodes/
│   │   │   │   │   ├── planner.py          # Query analysis
│   │   │   │   │   ├── retriever.py        # Data fetching
│   │   │   │   │   ├── analyzer.py         # Pattern finding
│   │   │   │   │   ├── critic.py           # Quality evaluation
│   │   │   │   │   ├── generator.py        # Output creation
│   │   │   │   │   └── responder.py        # Response formatting
│   │   │   │   ├── state.py                # ResearchState definition
│   │   │   │   └── workflow.py             # LangGraph wiring
│   │   │   ├── graph/
│   │   │   │   └── connection.py           # Neo4j connection
│   │   │   ├── config/
│   │   │   │   └── settings.py             # Environment config
│   │   │   ├── llm.py                      # LLM factory (Groq/Ollama)
│   │   │   └── interfaces/
│   │   │       └── cli.py                  # Command line interface
│   │   └── pyproject.toml
│   │
│   ├── mcp-financial/                      # Alpha Vantage MCP Server
│   │   ├── src/index.ts                    # MCP server implementation
│   │   └── package.json
│   │
│   └── google-slides-mcp/                  # Google Slides MCP Server
│       ├── src/index.ts                    # MCP server implementation
│       └── package.json
│
├── data/                                   # Sample documents for ingestion
│   └── microsoft-letters/                  # Shareholder letters 2020-2024
│
└── graph_ingestion_schemaorg.ipynb         # Knowledge graph ingestion notebook
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

2. **Select LLM provider** using the toggle:
   - Groq: Faster, but has rate limits
   - Ollama: Slower, but no limits

3. **Enter your question** in the search box

4. **Watch the progress** in the log viewer on the right

5. **View results** in the response panel on the left

6. **Download slides** if a presentation was generated (button appears in response)

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
- "Show me Apple's profit margins"

**Factual Questions:**
- "When did Microsoft invest in OpenAI?"
- "What products did Microsoft launch in 2023?"
- "Who is Microsoft's CEO?"

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
  "max_iterations": 3
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
| `retrieval` | Data retrieved from source |
| `insight` | Analysis insight generated |
| `decision` | Critic made a decision |
| `progress` | Iteration progress update |
| `final_response` | Final response ready |
| `complete` | All processing done |
| `error` | Error occurred |

**Example Event:**
```json
{
  "type": "retrieval",
  "session_id": "abc123",
  "source": "graph",
  "query": "Microsoft AI entities",
  "result_count": 23,
  "timestamp": "2024-01-15T10:30:05Z"
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

#### GET /api/download/{filename}

Download a generated PowerPoint presentation.

**Response:** Binary .pptx file

**Notes:**
- Files expire after 1 hour
- Filename must end with `.pptx`

#### GET /api/session/{session_id}

Get the current state of a session.

**Response:**
```json
{
  "session_id": "abc123",
  "query": "...",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "final_response": "...",
  "error": null
}
```

#### GET /api/debug/neo4j

Debug endpoint to check Neo4j connection.

**Response:**
```json
{
  "status": "connected",
  "node_labels": ["Entity", "Document", "Chunk"],
  "relationship_types": ["RELATED_TO", "MENTIONS"],
  "total_nodes": 1523,
  "total_relationships": 4892,
  "sample_nodes": [...]
}
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "slidekick",
  "version": "1.0.0",
  "model_loaded": true
}
```

---

## Output Formats

### Chat Response

Returned for factual, financial, and exploratory queries.

Format: Markdown text with headers, bullet points, and formatting.

### Slides (PowerPoint)

Returned for strategic and comparative queries.

**Slide Structure:**
1. **Title Slide** - Query summary and date
2. **Executive Summary** - Key findings overview
3. **Content Slides** (3-5) - Detailed analysis with bullets
4. **Conclusion** - Recommendations or summary

**Bullet Format:**
Each bullet follows "Key Point: Explanation" pattern with 20-35 words.

**Generation Priority:**
1. Google Slides API (creates shareable link)
2. python-pptx fallback (creates downloadable file)
3. Text-based slides (if both fail)

---

## Adding Your Own Data

### Knowledge Graph Ingestion

The demo uses Microsoft Shareholder Letters, but you can add your own documents.

**Step 1: Prepare Documents**

Place your documents in `data/your-folder/`:
- Supported: PDF, TXT, DOCX
- Recommended: Clean, structured text

**Step 2: Run Ingestion Notebook**

Open `graph_ingestion_schemaorg.ipynb` and modify:

```python
# Change the document path
DOCUMENTS_PATH = "data/your-folder/"

# Update entity extraction prompts if needed
ENTITY_TYPES = ["Company", "Product", "Person", "Technology"]
```

**Step 3: Execute All Cells**

The notebook will:
1. Load and chunk documents
2. Extract entities using LLM
3. Create relationships between entities
4. Store everything in Neo4j

**Step 4: Verify**

Check the debug endpoint:
```
GET /api/debug/neo4j
```

### Schema

The knowledge graph uses this schema:

**Node Labels:**
- `Entity` - Companies, products, people, technologies
- `Document` - Source documents
- `Chunk` - Document chunks for retrieval

**Relationships:**
- `RELATED_TO` - General relationship between entities
- `MENTIONS` - Document/chunk mentions entity
- `PART_OF` - Entity is part of another entity

---

## Deployment

### Frontend (Vercel)

**Step 1: Push to GitHub**

```bash
git push origin main
```

**Step 2: Connect to Vercel**

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Set root directory to `web`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-hf-space.hf.space
   ```
5. Deploy

### Backend (HuggingFace Spaces)

**Step 1: Create a Space**

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Create new Space
3. Select "Docker" as SDK
4. Set visibility (public or private)

**Step 2: Push API Code**

```bash
cd api
git init
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/slidekick
git add .
git commit -m "Initial deploy"
git push space main
```

**Step 3: Configure Secrets**

In Space Settings > Repository Secrets, add:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `GROQ_API_KEY`
- `TAVILY_API_KEY`
- `ALPHA_VANTAGE_API_KEY`

**Step 4: Verify**

Check the Space logs and visit `/health` endpoint.

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

**Cause:** Wrong credentials or database not running.

**Fix:**
1. Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env
2. Check if Neo4j is running: `GET /api/debug/neo4j`
3. For Aura: Ensure URI starts with `neo4j+s://`

#### "Groq rate limit reached"

**Cause:** Exceeded Groq's free tier limits.

**Fix:**
1. Switch to Ollama in the UI
2. Wait for the time shown in the error message
3. Consider upgrading Groq plan for higher limits

#### "No results from knowledge graph"

**Cause:** Graph is empty or query doesn't match entities.

**Fix:**
1. Check graph contents: `GET /api/debug/neo4j`
2. Run the ingestion notebook to populate data
3. Verify entity names match your documents

#### "Slides generation failed"

**Cause:** Google Slides API not configured or billing issue.

**Fix:**
1. python-pptx fallback should work automatically
2. Check if `python-pptx` is installed: `pip install python-pptx`
3. For Google Slides: Verify service account and billing

#### "Ollama connection refused"

**Cause:** Ollama server not running.

**Fix:**
```bash
ollama serve
# Then verify:
curl http://localhost:11434/api/tags
```

#### "Module not found: copilot"

**Cause:** Agent package not in Python path.

**Fix:**
```bash
cd packages/agent
pip install -e .
```

### Debug Mode

Enable detailed logging:

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
cd packages/agent
pytest tests/
```

### Code Structure

**Adding a new agent node:**

1. Create `packages/agent/src/copilot/agent/nodes/your_node.py`
2. Define the node function that takes and returns `ResearchState`
3. Add to workflow in `workflow.py`
4. Add edge connections

**Adding a new data source:**

1. Add retrieval logic in `retriever.py`
2. Add new field in `state.py` for results
3. Update analyzer to handle new data type

### Local Development with Hot Reload

**API:**
```bash
cd api
uvicorn main:app --reload --port 7860
```

**Web:**
```bash
cd web
npm run dev
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Submit a pull request

---

## Tech Stack

| Technology | Purpose | Documentation |
|------------|---------|---------------|
| **LangGraph** | Agent orchestration with conditional loops | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) |
| **LangChain** | LLM integration and prompts | [python.langchain.com](https://python.langchain.com/) |
| **Neo4j** | Knowledge graph database | [neo4j.com/docs](https://neo4j.com/docs/) |
| **Next.js 15** | React framework with App Router | [nextjs.org/docs](https://nextjs.org/docs) |
| **FastAPI** | Python API framework | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) |
| **SSE-Starlette** | Server-Sent Events for streaming | [github.com/sysid/sse-starlette](https://github.com/sysid/sse-starlette) |
| **Groq** | Fast LLM inference | [console.groq.com/docs](https://console.groq.com/docs) |
| **Ollama** | Local LLM server | [ollama.ai](https://ollama.ai/) |
| **Tavily** | AI-powered web search | [tavily.com](https://tavily.com/) |
| **Alpha Vantage** | Financial data API | [alphavantage.co/documentation](https://www.alphavantage.co/documentation/) |
| **python-pptx** | PowerPoint generation | [python-pptx.readthedocs.io](https://python-pptx.readthedocs.io/) |
| **Framer Motion** | React animations | [framer.com/motion](https://www.framer.com/motion/) |
| **shadcn/ui** | UI component library | [ui.shadcn.com](https://ui.shadcn.com/) |
| **Tailwind CSS** | Utility-first CSS | [tailwindcss.com](https://tailwindcss.com/) |

---

## License

MIT License - Use it however you want.

---

## Acknowledgments

- Microsoft Shareholder Letters used for demo knowledge graph
- LangChain team for LangGraph
- Anthropic, Groq, and Ollama for LLM access
