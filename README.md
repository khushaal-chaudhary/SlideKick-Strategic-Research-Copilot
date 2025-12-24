# Strategic Research Copilot

An AI research analyst that builds knowledge graphs from company documents, performs multi-step strategic analysis with self-reflection, and delivers findings as Google Slides presentations.

**Created by [Khushaal Chaudhary](https://khushaalchaudhary.com)** | [LinkedIn](https://linkedin.com/in/khushaal-chaudhary) | [GitHub](https://github.com/khushaal-chaudhary)

> **Live Demo:** [Coming Soon] | **Knowledge Graph:** Built from Microsoft Shareholder Letters (2020-2024)

## 🎯 What Makes This Genuinely Agentic

Unlike simple RAG pipelines, this system makes **real decisions at runtime**:

```
User: "How should we respond to Google's AI announcements?"

┌─────────────────────────────────────────────────────────────────┐
│ PLANNER: Decompose into research steps                          │
│   → Step 1: Get our AI strategy from graph                      │
│   → Step 2: Get competitor moves from graph                     │
│   → Step 3: Identify gaps                                       │
│   → Step 4: Generate recommendations                            │
├─────────────────────────────────────────────────────────────────┤
│ RETRIEVER: Execute Step 1                                       │
│   → Graph query: 23 AI-related entities found ✓                 │
├─────────────────────────────────────────────────────────────────┤
│ RETRIEVER: Execute Step 2                                       │
│   → Graph query: Only 5 Google entities ⚠️                      │
│   → DECISION: Sparse data → trigger web search                  │
│   → Web search: 12 additional results                           │
├─────────────────────────────────────────────────────────────────┤
│ ANALYZER: Synthesize findings                                   │
│   → Found 3 competitive gaps                                    │
│   → Generated strategic recommendations                         │
├─────────────────────────────────────────────────────────────────┤
│ CRITIC: Evaluate quality                                        │
│   → Confidence: 0.72 (below threshold)                          │
│   → DECISION: Need more data on "cloud AI" specifically         │
│   → LOOP BACK to retriever with refined query                   │
├─────────────────────────────────────────────────────────────────┤
│ CRITIC: Re-evaluate                                             │
│   → Confidence: 0.91 ✓                                          │
│   → Proceed to generation                                       │
├─────────────────────────────────────────────────────────────────┤
│ GENERATOR: Create deliverable                                   │
│   → DECISION: Strategic question → slides (not chat)            │
│   → Call Google Slides MCP                                      │
│   → Return shareable link                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI / API                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH ORCHESTRATOR                               │
│                                                                              │
│   ┌─────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐         │
│   │ PLANNER │ ──▶ │ RETRIEVER │ ──▶ │ ANALYZER │ ──▶ │  CRITIC   │         │
│   └─────────┘     └───────────┘     └──────────┘     └───────────┘         │
│        │               │                                   │                │
│        │               │    ┌──────────────────────────────┘                │
│        │               │    │                                               │
│        │               │    ▼                                               │
│        │               │  ┌─────────────────────────────────┐               │
│        │               │  │         DECISION POINT          │               │
│        │               │  │  ┌─────────┐    ┌───────────┐  │               │
│        │               │  │  │ ENOUGH? │    │ LOOP BACK │  │               │
│        │               │  │  └────┬────┘    └─────┬─────┘  │               │
│        │               │  │       │               │        │               │
│        │               │  └───────┼───────────────┼────────┘               │
│        │               │          │               │                         │
│        │               ◀──────────┼───────────────┘                         │
│        │                          ▼                                         │
│        │                    ┌───────────┐     ┌───────────┐                │
│        │                    │ GENERATOR │ ──▶ │ RESPONDER │                │
│        │                    └───────────┘     └───────────┘                │
│        │                          │                                         │
│        │                          ▼                                         │
│        │                    ┌───────────┐                                   │
│        │                    │    MCP    │                                   │
│        │                    │  SERVERS  │                                   │
│        │                    └───────────┘                                   │
└────────┼────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   NEO4J GRAPH   │  │  GOOGLE SLIDES  │  │ FINANCIAL DATA  │
│   + VECTORS     │  │   MCP (Existing)│  │ MCP (TypeScript)│
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📁 Project Structure

```
strategic-research-copilot/
│
├── web/                             # Next.js - Web Interface
│   ├── app/                         # App Router pages
│   ├── components/                  # React components
│   └── package.json
│
├── api/                             # FastAPI - Backend for HF Spaces
│   ├── main.py                      # API endpoints
│   ├── Dockerfile                   # HF Spaces deployment
│   └── requirements.txt
│
├── packages/
│   │
│   ├── agent/                       # Python - Core LangGraph Agent
│   │   ├── src/copilot/
│   │   │   ├── config/              # Settings & environment
│   │   │   ├── graph/               # Neo4j operations
│   │   │   ├── agent/               # LangGraph workflow
│   │   │   │   ├── state.py         # Research state definition
│   │   │   │   ├── nodes/           # Individual agent nodes
│   │   │   │   │   ├── planner.py   # Decomposes query into steps
│   │   │   │   │   ├── retriever.py # Gets data (graph/vector/web)
│   │   │   │   │   ├── analyzer.py  # Synthesizes insights
│   │   │   │   │   ├── critic.py    # Self-reflection & quality check
│   │   │   │   │   └── generator.py # Creates deliverables
│   │   │   │   ├── workflow.py      # LangGraph construction
│   │   │   │   └── decisions.py     # Routing logic
│   │   │   ├── tools/               # Tool definitions
│   │   │   └── interfaces/          # CLI
│   │   ├── notebooks/               # Development & testing
│   │   └── pyproject.toml
│   │
│   ├── mcp-financial/               # TypeScript - Financial Data MCP
│   │   └── src/index.ts             # Alpha Vantage integration
│   │
│   └── google-slides-mcp/           # Google Slides MCP Server
│
├── data/                            # Sample documents
└── README.md
```

## 🚀 Quick Start

```bash
# 1. Setup Python agent
cd packages/agent
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - GOOGLE_API_KEY (for LLM)
# - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD (for knowledge graph)
# - TAVILY_API_KEY (for web search)
# - ALPHA_VANTAGE_API_KEY (for financial data - free at alphavantage.co)

# 3. Run the agent
copilot chat
```

## 💰 Financial Data Capabilities

The agent can retrieve real-time financial data using the Alpha Vantage API:

```
User: "What is Microsoft's P/E ratio and how does it compare to Apple?"

┌─────────────────────────────────────────────────────────────────┐
│ PLANNER: Classify as FINANCIAL query                            │
│   → Use FINANCIAL_FIRST retrieval strategy                      │
├─────────────────────────────────────────────────────────────────┤
│ RETRIEVER: Fetch financial data                                 │
│   → GET company overview for MSFT                               │
│   → GET company overview for AAPL                               │
│   → P/E, EPS, profit margin, market cap                         │
├─────────────────────────────────────────────────────────────────┤
│ ANALYZER: Synthesize financial insights                         │
│   → Compare valuation metrics                                   │
│   → Generate investment insights                                │
├─────────────────────────────────────────────────────────────────┤
│ GENERATOR: Create response with financial data                  │
└─────────────────────────────────────────────────────────────────┘
```

**Available Financial Data:**
- Company overview and fundamentals
- Stock quotes (price, change, volume)
- Income statement data
- News sentiment analysis
- Multi-company comparisons

**Setup:** Get a free API key at [alphavantage.co](https://www.alphavantage.co/support/#api-key)

## 📚 Knowledge Graph

The demo knowledge graph is built from **Microsoft Shareholder Letters (2020-2024)**, containing:
- Company strategy and vision
- Product announcements and launches
- Financial highlights and metrics
- Competitive landscape mentions

**Want to use your own data?** Clone this repo and:
1. Add your documents to `data/`
2. Run the ingestion pipeline to build your knowledge graph
3. Update Neo4j connection in `.env`

## 🔧 Technologies

| Technology | Purpose | Why It's Needed |
|------------|---------|-----------------|
| **LangGraph** | Agent orchestration | Multi-step research with loops and decisions |
| **Neo4j** | Knowledge graph | Entity relationships for strategic analysis |
| **Next.js** | Web interface | Modern React framework with SSR |
| **FastAPI** | Backend API | High-performance Python API |
| **LangSmith** | Observability | Debug complex agent traces |
| **MCP** | Tool integration | Google Slides, financial data APIs |
| **Alpha Vantage** | Financial data | Stock quotes, fundamentals, income statements |
| **Tavily** | Web search | Real-time information retrieval |
| **Hugging Face Spaces** | API hosting | Free ML/AI model deployment |
| **Vercel** | Frontend hosting | Edge-optimized React deployment |

## 📊 LangSmith Traces

All agent runs are traced for debugging and evaluation:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=strategic-research-copilot
```

## 📝 License

MIT
