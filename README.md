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

# SlideKick ⚡

**Research that kicks!** Your AI sidekick that digs through knowledge graphs, crunches data, argues with itself, and delivers killer insights. No coffee breaks needed.

**Created by [Khushaal Chaudhary](https://khushaalchaudhary.com)** | [LinkedIn](https://linkedin.com/in/khushaal-chaudhary) | [GitHub](https://github.com/khushaal-chaudhary)

> **Live Demo:** [Coming Soon] | **Knowledge Graph:** Built from Microsoft Shareholder Letters (2020-2024)

## 🎯 What Makes This Actually Smart

Unlike basic RAG pipelines that just retrieve and regurgitate, SlideKick makes **real decisions at runtime**:

```
You: "How should we clap back at Google's AI moves?"

┌─────────────────────────────────────────────────────────────────┐
│ 🧭 PLANNER: Breaking this down...                               │
│   → Step 1: Dig up our AI strategy from the graph               │
│   → Step 2: Scout competitor moves                              │
│   → Step 3: Find the gaps they're missing                       │
│   → Step 4: Cook up some recommendations                        │
├─────────────────────────────────────────────────────────────────┤
│ 🦮 RETRIEVER: Fetching Step 1...                                │
│   → Graph query: 23 AI-related entities found ✓                 │
├─────────────────────────────────────────────────────────────────┤
│ 🦮 RETRIEVER: Fetching Step 2...                                │
│   → Graph query: Only 5 Google entities ⚠️                      │
│   → Hmm, sparse data. Let me hit the web...                     │
│   → Web search: 12 fresh results found!                         │
├─────────────────────────────────────────────────────────────────┤
│ 🔬 ANALYZER: Connecting the dots...                             │
│   → Spotted 3 competitive gaps                                  │
│   → Strategic recommendations forming...                        │
├─────────────────────────────────────────────────────────────────┤
│ 🎭 CRITIC: Let me be honest here...                             │
│   → Confidence: 0.72 (not good enough)                          │
│   → Need deeper data on "cloud AI" specifically                 │
│   → Sending retriever back for more! 🔄                         │
├─────────────────────────────────────────────────────────────────┤
│ 🎭 CRITIC: Much better now!                                     │
│   → Confidence: 0.91 ✓                                          │
│   → Ship it!                                                    │
├─────────────────────────────────────────────────────────────────┤
│ ⚡ GENERATOR: Time to create magic...                           │
│   → Strategic question detected → making slides                 │
│   → Calling Google Slides API...                                │
│   → Done! Here's your shareable link 🔗                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ How The Magic Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEB UI / API                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH BRAIN                                      │
│                                                                              │
│   ┌─────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐         │
│   │ 🧭      │ ──▶ │ 🦮        │ ──▶ │ 🔬       │ ──▶ │ 🎭        │         │
│   │ Planner │     │ Retriever │     │ Analyzer │     │ Critic    │         │
│   └─────────┘     └───────────┘     └──────────┘     └───────────┘         │
│        │               │                                   │                │
│        │               │         ┌─────────────────────────┘                │
│        │               │         │                                          │
│        │               │         ▼                                          │
│        │               │    ┌──────────────┐                                │
│        │               │    │ Good enough? │                                │
│        │               │    │  YES │ NO    │                                │
│        │               │    └──────┼───────┘                                │
│        │               │           │                                        │
│        │               ◀───────────┘ (Loop back if NO!)                     │
│        │                                                                    │
│        │                    ┌───────────┐     ┌───────────┐                │
│        │                    │ ⚡        │ ──▶ │ 📤        │                │
│        │                    │ Generator │     │ Responder │                │
│        │                    └───────────┘     └───────────┘                │
└────────┼────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   NEO4J GRAPH   │  │  GOOGLE SLIDES  │  │ FINANCIAL DATA  │
│   + VECTORS     │  │    (MCP)        │  │    (MCP)        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📁 Project Structure

```
slidekick/
│
├── web/                             # Next.js - Pretty Face
│   ├── app/                         # App Router pages
│   ├── components/                  # React components
│   └── package.json
│
├── api/                             # FastAPI - Speed Demon
│   ├── main.py                      # API endpoints + SSE
│   ├── Dockerfile                   # HF Spaces deployment
│   └── requirements.txt
│
├── packages/
│   │
│   ├── agent/                       # Python - The Brains
│   │   ├── src/copilot/
│   │   │   ├── config/              # Settings & secrets
│   │   │   ├── graph/               # Neo4j operations
│   │   │   ├── agent/               # LangGraph workflow
│   │   │   │   ├── state.py         # Research state
│   │   │   │   ├── nodes/           # The squad
│   │   │   │   │   ├── planner.py   # 🧭 Game plan maker
│   │   │   │   │   ├── retriever.py # 🦮 Data fetcher
│   │   │   │   │   ├── analyzer.py  # 🔬 Pattern finder
│   │   │   │   │   ├── critic.py    # 🎭 Quality cop
│   │   │   │   │   └── generator.py # ⚡ Magic maker
│   │   │   │   └── workflow.py      # LangGraph wiring
│   │   │   └── interfaces/          # CLI
│   │   └── pyproject.toml
│   │
│   ├── mcp-financial/               # Alpha Vantage MCP
│   │
│   └── google-slides-mcp/           # Slide Wizard MCP
│
└── data/                            # Sample documents
```

## 🚀 Quick Start

```bash
# 1. Setup the brain
cd packages/agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"

# 2. Feed it your secrets
cp .env.example .env
# Edit .env with:
# - LLM_PROVIDER=ollama (or gemini)
# - LLM_MODEL=qwen2.5:7b
# - NEO4J credentials
# - TAVILY_API_KEY (for web search)
# - ALPHA_VANTAGE_API_KEY (free at alphavantage.co)

# 3. Let it rip!
copilot chat
```

## 💰 Money Talks: Financial Data

SlideKick can fetch real-time financial data and sound smart about stocks:

```
You: "What's Microsoft's P/E and how does it stack up against Apple?"

┌─────────────────────────────────────────────────────────────────┐
│ 🧭 PLANNER: Financial question detected!                        │
│   → Using MONEY_FIRST strategy                                  │
├─────────────────────────────────────────────────────────────────┤
│ 🦮 RETRIEVER: Hitting the markets...                            │
│   → GET company overview: MSFT                                  │
│   → GET company overview: AAPL                                  │
│   → P/E, EPS, margins, market cap - all here!                   │
├─────────────────────────────────────────────────────────────────┤
│ 🔬 ANALYZER: Crunching numbers...                               │
│   → Comparing valuations                                        │
│   → Spotting investment angles                                  │
├─────────────────────────────────────────────────────────────────┤
│ ⚡ GENERATOR: Here's the scoop...                                │
└─────────────────────────────────────────────────────────────────┘
```

**What it knows:**
- Company fundamentals (the boring but important stuff)
- Stock quotes (price, change, volume)
- Income statements
- News sentiment (what people are saying)
- Cross-company comparisons

**Get your free key:** [alphavantage.co](https://www.alphavantage.co/support/#api-key)

## 📚 The Knowledge Graph

Demo is loaded with **Microsoft Shareholder Letters (2020-2024)** covering:
- Strategy and vision stuff
- Product launches and announcements
- Financial highlights
- Competitive landscape intel

**Want to use your own data?** Fork this repo and:
1. Drop your docs in `data/`
2. Run the ingestion pipeline
3. Update Neo4j creds in `.env`
4. Start kicking!

## 🔧 The Tech Stack

| Tech | Role | Why We Need It |
|------|------|----------------|
| **LangGraph** | Brain Power | Multi-step thinking with loops |
| **Neo4j** | Memory Palace | Connecting the dots |
| **Next.js** | Pretty Face | Sleek React frontend |
| **FastAPI** | Speed Demon | Blazing Python backend |
| **Ollama** | Local Brain | Run LLMs on your machine |
| **LangSmith** | X-Ray Vision | Debug the AI's thoughts |
| **Alpha Vantage** | Money Talks | Real-time financials |
| **Tavily** | Web Crawler | Fresh info from the web |
| **HF Spaces** | Cloud Home | API hosting |
| **Vercel** | Edge Runner | Frontend hosting |

## 📊 Watch The AI Think (LangSmith)

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=slidekick
```

## 📝 License

MIT - Go wild! 🎉
