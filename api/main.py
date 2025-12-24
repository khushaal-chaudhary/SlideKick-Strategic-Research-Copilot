"""
Strategic Research Copilot API

FastAPI server for Hugging Face Spaces deployment.
Provides endpoints for the web interface to interact with the research agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =============================================================================
# App Configuration
# =============================================================================

app = FastAPI(
    title="Strategic Research Copilot API",
    description="AI-powered research analyst with knowledge graph, financial data, and web search capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local Next.js dev
        "https://*.vercel.app",   # Vercel deployments
        "https://khushaalchaudhary.com",  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "strategic-research-copilot"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Strategic Research Copilot API",
        "version": "1.0.0",
        "description": "AI research analyst with multi-step reasoning",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "query": "/api/query (POST)",
            "stream": "/api/stream/{session_id} (SSE)",
        }
    }

# =============================================================================
# API Routes (to be implemented in Step 1.3)
# =============================================================================

# TODO: Add /api/query endpoint
# TODO: Add /api/stream/{session_id} SSE endpoint
# TODO: Add agent integration
