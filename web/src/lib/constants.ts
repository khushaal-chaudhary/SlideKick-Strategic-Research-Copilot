/**
 * Site Configuration & Personal Information
 * SlideKick - Research that kicks!
 */

export const SITE_CONFIG = {
  name: "SlideKick",
  tagline: "Research that kicks!",
  description:
    "Your AI research sidekick that digs through knowledge graphs, crunches data, argues with itself, and delivers killer insights. No coffee breaks needed.",
  author: "Khushaal Chaudhary",
  url: "https://khushaalchaudhary.com",
} as const;

export const PERSONAL_INFO = {
  name: "Khushaal Chaudhary",
  email: "khushaalchaudhary@outlook.com",
  website: "https://khushaalchaudhary.com",
  linkedin: "https://linkedin.com/in/khushaal-chaudhary",
  github: "https://github.com/khushaal-chaudhary",
} as const;

export const TECH_STACK = [
  {
    name: "LangGraph",
    category: "Brain Power",
    description: "Multi-step reasoning with self-reflection loops",
    icon: "workflow",
  },
  {
    name: "Neo4j",
    category: "Memory Palace",
    description: "Knowledge graph for connecting the dots",
    icon: "database",
  },
  {
    name: "Next.js",
    category: "Pretty Face",
    description: "Sleek React frontend that just works",
    icon: "globe",
  },
  {
    name: "FastAPI",
    category: "Speed Demon",
    description: "Blazing fast Python backend with real-time streaming",
    icon: "server",
  },
  {
    name: "Alpha Vantage",
    category: "Money Talks",
    description: "Real-time stock data and financials",
    icon: "trending-up",
  },
  {
    name: "Tavily",
    category: "Web Crawler",
    description: "AI-powered search that finds the good stuff",
    icon: "search",
  },
  {
    name: "Google Slides",
    category: "Slide Wizard",
    description: "Auto-generates presentations like magic",
    icon: "presentation",
  },
  {
    name: "Hugging Face",
    category: "Cloud Home",
    description: "Where the AI models live and thrive",
    icon: "cloud",
  },
] as const;

export const AGENT_NODES = [
  {
    id: "planner",
    name: "Planner",
    emoji: "🧭",
    description: "Maps out the research game plan",
    color: "blue",
  },
  {
    id: "retriever",
    name: "Retriever",
    emoji: "🦮",
    description: "Fetches data like a good boy",
    color: "green",
  },
  {
    id: "analyzer",
    name: "Analyzer",
    emoji: "🔬",
    description: "Finds patterns humans miss",
    color: "purple",
  },
  {
    id: "critic",
    name: "Critic",
    emoji: "🎭",
    description: "The tough love quality checker",
    color: "orange",
  },
  {
    id: "generator",
    name: "Generator",
    emoji: "⚡",
    description: "Turns insights into gold",
    color: "pink",
  },
] as const;

export const EXAMPLE_QUERIES = [
  "What is Microsoft's AI strategy based on their shareholder letters?",
  "How did Microsoft's cloud business evolve from 2020 to 2024?",
  "What are the recurring themes in Microsoft's annual shareholder letters?",
  "How is Microsoft positioning against competitors?",
  "Compare Microsoft (MSFT) and Apple (AAPL) P/E ratios",
] as const;

export const FUTURE_ITERATIONS = [
  {
    title: "LangSmith Tracing",
    description: "Watch the AI think in real-time with full observability",
    status: "planned",
  },
  {
    title: "BYOD (Bring Your Own Docs)",
    description: "Upload your docs, we'll build the knowledge graph",
    status: "planned",
  },
  {
    title: "Memory Mode",
    description: "Follow-up questions that actually remember context",
    status: "planned",
  },
  {
    title: "Export Anywhere",
    description: "Ship findings to PDF, Notion, or wherever you want",
    status: "idea",
  },
  {
    title: "Team Mode",
    description: "Research together, discover together",
    status: "idea",
  },
] as const;

export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860",
  streamEndpoint: "/api/stream",
  queryEndpoint: "/api/query",
  healthEndpoint: "/health",
} as const;

// Fun loading messages for the status indicator
export const LOADING_MESSAGES = [
  "Warming up the neurons...",
  "Teaching AI to read...",
  "Downloading more RAM...",
  "Asking the knowledge graph nicely...",
  "Convincing the model to cooperate...",
] as const;
