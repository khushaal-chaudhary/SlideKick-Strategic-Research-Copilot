"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import {
  Brain,
  ChevronDown,
  Database,
  Gauge,
  Radio,
  Search,
  Server,
  Upload,
} from "lucide-react";

interface WikiEntry {
  question: string;
  answer: string;
}

interface WikiSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  entries: WikiEntry[];
}

const SECTIONS: WikiSection[] = [
  {
    id: "agent",
    title: "Architecture & Agent Design",
    icon: <Brain className="h-4 w-4" />,
    entries: [
      {
        question: "What is SlideKick, in one paragraph?",
        answer:
          "SlideKick is a GraphRAG research copilot. A LangGraph agent plans each query, retrieves from a Neo4j knowledge graph built from Microsoft shareholder letters (2020–2024) alongside vector search, live web search, and financial APIs, then critiques its own draft and loops back for more data when the quality is not good enough. Everything — node transitions, retrieval hits, the critic's decisions, and the answer itself token by token — streams live to this page.",
      },
      {
        question: "Why an agent instead of a single RAG pipeline?",
        answer:
          "Different questions need different data. \"What is MSFT's P/E ratio?\" needs a financial API, \"How did Microsoft's AI strategy evolve?\" needs the knowledge graph, and \"What did Microsoft announce last week?\" needs the web. A fixed retrieve-then-generate pipeline can't make that call, and it can't notice that its first retrieval came back thin. The agent's planner picks a retrieval strategy per query, and the critic loop detects insufficient evidence and chooses which tool to try next.",
      },
      {
        question: "Why LangGraph?",
        answer:
          "The workflow is genuinely a graph: conditional edges express the critic's loop-back decision, returning a list of node names from a routing function fans retrieval out in parallel, and state reducers merge the parallel results deterministically. LangGraph also streams in two modes at once — per-node state updates and raw LLM tokens — which maps one-to-one onto the SSE events the frontend renders. Hand-rolling that control flow around plain function calls would reinvent a worse version of the same thing.",
      },
      {
        question: "How does the critic loop (self-reflection) work?",
        answer:
          "After the analyzer synthesizes retrieved evidence, a critic node scores the synthesis from 0 to 1 against the original question, lists the gaps it found, and decides: good enough → generate the answer, or insufficient → pick exactly one refinement tool (web search, deeper graph exploration, vector search, or financial data) with an optimized query for it. The workflow routes back to that single retrieval node and the cycle repeats, capped at 3 iterations so a hard question can't loop forever.",
      },
      {
        question: "Which LLMs does it use, and why two providers?",
        answer:
          "Ollama runs qwen2.5:7b inside the same container — free, no rate limits, but CPU-slow. Groq serves llama-3.3-70b at very high speed on a free tier capped at 30 requests/minute. The demo defaults to Ollama so it can never be rate-limited into failure; the Groq toggle shows the fast path. The provider choice travels with each request through the agent's state, so concurrent users on different providers never interfere.",
      },
    ],
  },
  {
    id: "graph",
    title: "Knowledge Graph & Retrieval",
    icon: <Database className="h-4 w-4" />,
    entries: [
      {
        question: "Why a knowledge graph instead of plain vector RAG?",
        answer:
          "Vector search answers \"find me text that sounds like this question.\" It struggles with relationship questions — \"what connects Microsoft's OpenAI partnership to Azure revenue?\" — because the evidence is spread across chunks that don't individually resemble the query. A graph stores entities once and relationships explicitly, so multi-hop questions become traversals. Vector search is still in the loop for prose-heavy questions; the planner and critic choose between them.",
      },
      {
        question: "Why schema.org as the graph schema?",
        answer:
          "LLM-based entity extraction with an open-ended label set produces label soup — every run invents new node types. Constraining extraction to schema.org types (Organization, Product, Person, Event…) gives the model a finite vocabulary it already knows from pretraining, which makes extraction far more consistent. A post-ingestion pruning pass removes anything that still lands off-schema.",
      },
      {
        question: "Why Neo4j Aura?",
        answer:
          "Aura's free tier includes native vector indexes alongside the graph, so one database serves both graph traversal and semantic search — including a second vector index for user-uploaded documents. That halves the infrastructure for a project that must run entirely on free tiers.",
      },
      {
        question: "How does hybrid retrieval actually run?",
        answer:
          "The planner classifies the query and picks a strategy. For hybrid strategies, graph and vector retrieval run in parallel as separate LangGraph nodes — each returns only its delta, and reducers on the state concatenate them. Web search and financial data join the fan-out when the strategy or the critic calls for them. All sources then converge at a reranking node.",
      },
      {
        question: "Why cross-encoder reranking, and why ms-marco-MiniLM-L-6-v2?",
        answer:
          "Graph hits, vector chunks, and web results carry scores that mean different things — cosine similarity is not a Tavily relevance score is not a graph match. The reranker flattens all candidates to text and scores each (query, candidate) pair with a cross-encoder, producing one comparable ranking; the analyzer reads the top 15. ms-marco-MiniLM-L-6-v2 is the standard small reranker: strong on passage ranking, fast on free CPU, and baked into the Docker image so there's no cold-start download.",
      },
    ],
  },
  {
    id: "evals",
    title: "Evaluation & Quality",
    icon: <Gauge className="h-4 w-4" />,
    entries: [
      {
        question: "How is answer quality measured?",
        answer:
          "An eval harness runs the full agent over a golden dataset of research queries with expected facts. An LLM judge scores each answer on faithfulness (is every claim supported by retrieved context?), context precision (was the retrieval relevant?), fact recall (did it surface the expected facts?), and overall answer quality. Results are versioned in the repo and published on the Metrics page.",
      },
      {
        question: "Why judge with a different model family than the agent?",
        answer:
          "A model grading its own family's output inherits its blind spots — a Llama judge tends to like Llama answers. Judging with a separate family breaks that correlation, and as a bonus keeps eval runs from consuming the same rate-limited quota the live demo depends on.",
      },
      {
        question: "What is critic calibration and why track it?",
        answer:
          "The agent's critic assigns itself a quality score before answering. Critic calibration is the correlation between those self-scores and the external judge's scores. It answers a question most agent demos skip: is the self-reflection loop actually measuring quality, or just performing it? If the correlation collapses, the critic's loop-back decisions are noise — so this metric guards the core mechanism of the system.",
      },
    ],
  },
  {
    id: "byod",
    title: "Bring Your Own Documents",
    icon: <Upload className="h-4 w-4" />,
    entries: [
      {
        question: "What happens when I upload a document?",
        answer:
          "The pipeline parses the PDF or text, chunks it with the same parameters as the demo corpus, extracts schema.org entities and relationships with an LLM (Gemini Flash, falling back to Groq), embeds the chunks, and MERGEs everything into the graph under your workspace's namespace. Each stage streams progress over SSE, so you watch the ingestion happen. Your next queries then retrieve from your documents and the demo corpus together.",
      },
      {
        question: "How is the demo corpus protected from uploads?",
        answer:
          "Every uploaded node carries a namespace property (a client-side workspace UUID) and UserDoc/UserChunk labels, and user chunks live in their own vector index. Retrieval filters to \"no namespace OR your namespace,\" so uploads are invisible to other visitors and the curated corpus is never mutated. Workspaces are purged after 24 hours to stay inside Aura's free node budget.",
      },
      {
        question: "Why namespaces in one database instead of a database per user?",
        answer:
          "Aura's free tier allows exactly one database. Namespacing by property gets logical isolation with a single WHERE clause on every query — parameterized, so there's no injection path — while keeping the demo corpus and user data physically co-located where the same indexes and retrieval code serve both.",
      },
    ],
  },
  {
    id: "streaming",
    title: "Streaming & UX",
    icon: <Radio className="h-4 w-4" />,
    entries: [
      {
        question: "How does live progress reach the browser?",
        answer:
          "The agent runs in a background thread, streaming LangGraph events into a queue that an async generator drains into Server-Sent Events. Per-node state deltas become typed events — node transitions, retrieval results with reranker scores, the critic's decision and reasoning — and the generator's LLM tokens are forwarded as they're produced, so the answer types itself out instead of appearing after a long silence.",
      },
      {
        question: "Why SSE instead of WebSockets?",
        answer:
          "The data flows one way: server to browser. SSE does exactly that over plain HTTP — it passes through the Hugging Face Spaces proxy without special handling, EventSource reconnects automatically, and there's no connection-upgrade machinery to maintain. WebSockets would add bidirectional plumbing this app never uses.",
      },
      {
        question: "Why is the transparency itself a feature?",
        answer:
          "On free CPU inference, a research query takes real time. Showing the agent's actual behavior — which sources it chose, what the reranker promoted, why the critic looped back — turns that wait into the demo. The log viewer isn't decoration; it's the agent's genuine event stream.",
      },
    ],
  },
  {
    id: "infra",
    title: "Infrastructure & Tradeoffs",
    icon: <Server className="h-4 w-4" />,
    entries: [
      {
        question: "What does this cost to run?",
        answer:
          "Zero. The API and Ollama share a free Hugging Face Spaces CPU container, the frontend is on Vercel's free tier, the graph lives in Neo4j Aura Free, and Groq, Gemini, Tavily, and Alpha Vantage are all on free API tiers. Nearly every architectural decision here — local inference, one database, CPU-sized reranker, batched extraction — traces back to that constraint.",
      },
      {
        question: "Why run Ollama inside the API container?",
        answer:
          "It gives the demo an inference path with no rate limits and no billing surprises: qwen2.5:7b for generation and nomic-embed-text for the 768-dim embeddings the vector indexes use. One container also means embeddings at query time and at ingestion time come from the identical model, which vector search correctness depends on.",
      },
      {
        question: "How does the system survive restarts and concurrent users?",
        answer:
          "Sessions snapshot to SQLite at every lifecycle transition, so a Space restart doesn't orphan session lookups — interrupted sessions resurface as explicit errors rather than hanging. Per-request state (LLM provider, workspace) travels through the agent's state object instead of module globals, and each SSE stream gets its own thread-safe queue, so concurrent queries can't cross-contaminate.",
      },
      {
        question: "What breaks first at scale?",
        answer:
          "Known limits, in order: CPU inference throughput (one 7B model, a few concurrent queries), Groq's 30 req/min when everyone picks the fast provider, Aura's node budget under heavy BYOD use (mitigated by the 24h TTL), and SQLite on the Space's ephemeral disk (fine for restarts, not for redeploys). The production upgrades are boring and known — GPU inference, Redis, a paid graph tier — which is exactly why the free-tier version is the interesting engineering problem.",
      },
      {
        question: "Why is there no human-in-the-loop step?",
        answer:
          "It was considered and rejected: this demo must run unattended for a visitor who won't answer clarifying questions. The critic loop fills the role a human reviewer would — evaluating drafts and requesting more evidence — automatically. In an enterprise deployment, the same LangGraph structure would accept a human checkpoint via an interrupt before generation.",
      },
    ],
  },
];

function WikiItem({ entry }: { entry: WikiEntry }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border/40 last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 py-3.5 text-left text-sm font-medium hover:text-primary transition-colors"
        aria-expanded={open}
      >
        {entry.question}
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      {open && (
        <motion.p
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.15 }}
          className="pb-4 text-sm leading-relaxed text-muted-foreground"
        >
          {entry.answer}
        </motion.p>
      )}
    </div>
  );
}

export function WikiContent() {
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return SECTIONS;
    return SECTIONS.map((section) => ({
      ...section,
      entries: section.entries.filter(
        (e) =>
          e.question.toLowerCase().includes(q) ||
          e.answer.toLowerCase().includes(q)
      ),
    })).filter((section) => section.entries.length > 0);
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search questions and answers..."
          className="pl-9"
        />
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No entries match &quot;{filter}&quot;.
        </p>
      )}

      {filtered.map((section) => (
        <Card key={section.id} className="border-border/50 shadow-subtle">
          <CardHeader className="py-4 px-5 border-b">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              {section.icon}
              {section.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-5 py-1">
            {section.entries.map((entry) => (
              <WikiItem key={entry.question} entry={entry} />
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
