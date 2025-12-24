"""
Strategic Research Copilot API

FastAPI server for Hugging Face Spaces deployment.
Provides endpoints for the web interface to interact with the research agent.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from config import get_settings
from schemas import (
    APIInfoResponse,
    AgentNode,
    DecisionEvent,
    ErrorEvent,
    EventType,
    FinalResponseEvent,
    HealthResponse,
    InsightEvent,
    NodeEvent,
    OutputEvent,
    ProgressEvent,
    QueryRequest,
    QueryResponse,
    RetrievalEvent,
    SessionState,
)

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# App Configuration
# =============================================================================

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    description="Research that kicks! AI sidekick with knowledge graphs, self-reflection, and killer insights.",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# In-Memory Session Store (for demo - use Redis in production)
# =============================================================================

sessions: dict[str, SessionState] = {}

# =============================================================================
# Health Check & Info Endpoints
# =============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    return HealthResponse(version=settings.api_version)


@app.get("/", response_model=APIInfoResponse)
async def root():
    """Root endpoint with API info."""
    return APIInfoResponse()


# =============================================================================
# Query Endpoints
# =============================================================================


@app.post("/api/query", response_model=QueryResponse)
async def submit_query(request: QueryRequest):
    """
    Submit a research query for processing.

    Returns a session ID that can be used to stream real-time updates.
    """
    session_id = str(uuid.uuid4())

    # Create session state
    session = SessionState(
        session_id=session_id,
        query=request.query,
        status="pending",
    )
    sessions[session_id] = session

    logger.info(f"New query submitted: {session_id} - {request.query[:50]}...")

    return QueryResponse(
        session_id=session_id,
        query=request.query,
        status="pending",
        stream_url=f"/api/stream/{session_id}",
    )


@app.get("/api/stream/{session_id}")
async def stream_events(session_id: str):
    """
    Stream real-time events for a research session using Server-Sent Events.

    This endpoint provides live updates as the agent processes the query,
    including node transitions, retrieval results, insights, and the final response.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events for the research session."""
        session = sessions[session_id]

        try:
            # Mark session as processing
            session.status = "processing"

            # Emit start event
            yield {
                "event": EventType.START.value,
                "data": json.dumps(
                    {
                        "type": EventType.START.value,
                        "session_id": session_id,
                        "query": session.query,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            }

            # =================================================================
            # Demo Flow: Simulate agent execution
            # In production, this integrates with the actual LangGraph agent
            # =================================================================

            # Node 1: Planner
            yield await _emit_node_event(
                session_id,
                AgentNode.PLANNER,
                "start",
                "Analyzing query and extracting key entities...",
            )
            await asyncio.sleep(1.5)
            yield await _emit_node_event(
                session_id,
                AgentNode.PLANNER,
                "complete",
                "Query analyzed. Identified 3 entities: Microsoft, AI Strategy, Annual Reports",
                {"entities": ["Microsoft", "AI Strategy", "Annual Reports"]},
            )

            # Progress update
            yield await _emit_progress(session_id, 1, 3, "Starting data retrieval...")

            # Node 2: Retriever
            yield await _emit_node_event(
                session_id,
                AgentNode.RETRIEVER,
                "start",
                "Querying knowledge graph...",
            )
            await asyncio.sleep(2.0)
            yield await _emit_retrieval(
                session_id,
                "graph",
                "Microsoft AI investments 2020-2024",
                8,
                [
                    {"entity": "Azure AI", "relationship": "major investment"},
                    {"entity": "OpenAI Partnership", "year": "2023"},
                ],
            )
            yield await _emit_node_event(
                session_id,
                AgentNode.RETRIEVER,
                "complete",
                "Retrieved 8 relevant entities from knowledge graph",
            )

            # Node 3: Analyzer
            yield await _emit_node_event(
                session_id,
                AgentNode.ANALYZER,
                "start",
                "Synthesizing retrieved information...",
            )
            await asyncio.sleep(1.8)
            yield await _emit_insight(
                session_id,
                "strategic_theme",
                "AI-First Strategy",
                "Microsoft has shifted to an AI-first approach across all product lines",
                0.92,
            )
            yield await _emit_insight(
                session_id,
                "investment_pattern",
                "Cloud + AI Integration",
                "Azure AI services revenue grew 40% YoY in 2024",
                0.88,
            )
            yield await _emit_node_event(
                session_id,
                AgentNode.ANALYZER,
                "complete",
                "Analysis complete. Generated 2 key insights.",
            )

            # Node 4: Critic
            yield await _emit_node_event(
                session_id, AgentNode.CRITIC, "start", "Evaluating research quality..."
            )
            await asyncio.sleep(1.2)
            yield await _emit_decision(
                session_id,
                "sufficient",
                "Quality score: 0.85. Threshold met.",
                "Proceeding to generate response",
            )
            yield await _emit_node_event(
                session_id,
                AgentNode.CRITIC,
                "complete",
                "Quality assessment: 85% - proceeding to generation",
                {"quality_score": 0.85},
            )

            # Progress update
            yield await _emit_progress(
                session_id, 2, 3, "Generating response...", 0.85
            )

            # Node 5: Generator
            yield await _emit_node_event(
                session_id,
                AgentNode.GENERATOR,
                "start",
                "Generating comprehensive response...",
            )
            await asyncio.sleep(2.0)
            yield await _emit_output(
                session_id,
                "chat",
                "Microsoft's AI strategy has evolved significantly from 2020 to 2024...",
            )
            yield await _emit_node_event(
                session_id, AgentNode.GENERATOR, "complete", "Response generated"
            )

            # Node 6: Responder
            yield await _emit_node_event(
                session_id, AgentNode.RESPONDER, "start", "Formatting final response..."
            )
            await asyncio.sleep(0.8)

            # Final response
            final_response = """## Microsoft's AI Strategy Evolution (2020-2024)

### Key Findings

**1. Strategic Partnership with OpenAI**
Microsoft's $10B+ investment in OpenAI has become the cornerstone of their AI strategy, integrating GPT models across their product suite.

**2. Azure AI Services Expansion**
- Azure AI revenue grew 40% YoY in 2024
- Launched Azure OpenAI Service for enterprise customers
- Copilot integration across Microsoft 365

**3. Product Integration**
- GitHub Copilot reached 1M+ paid subscribers
- Microsoft 365 Copilot launched for enterprise
- Bing Chat (now Copilot) reimagined search

### Timeline
- **2020**: Initial OpenAI partnership, focus on Azure ML
- **2021**: GitHub Copilot preview launched
- **2022**: DALL-E integration, Azure OpenAI preview
- **2023**: $10B OpenAI investment, Copilot everywhere
- **2024**: Copilot+ PCs, AI infrastructure expansion

*Sources: Microsoft Shareholder Letters 2020-2024*"""

            yield await _emit_final_response(
                session_id,
                final_response,
                0.85,
                2,
                ["knowledge_graph", "shareholder_letters"],
            )

            yield await _emit_node_event(
                session_id, AgentNode.RESPONDER, "complete", "Response delivered"
            )

            # Complete event
            session.status = "completed"
            session.final_response = final_response
            yield {
                "event": EventType.COMPLETE.value,
                "data": json.dumps(
                    {
                        "type": EventType.COMPLETE.value,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Error in session {session_id}: {e}")
            session.status = "error"
            session.error = str(e)
            yield {
                "event": EventType.ERROR.value,
                "data": json.dumps(
                    {
                        "type": EventType.ERROR.value,
                        "session_id": session_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            }

    return EventSourceResponse(event_generator())


# =============================================================================
# Helper Functions for Event Emission
# =============================================================================


async def _emit_node_event(
    session_id: str,
    node: AgentNode,
    action: str,
    message: str,
    metadata: dict | None = None,
) -> dict:
    """Emit a node start/complete event."""
    event_type = EventType.NODE_START if action == "start" else EventType.NODE_COMPLETE
    return {
        "event": event_type.value,
        "data": json.dumps(
            {
                "type": event_type.value,
                "session_id": session_id,
                "node": node.value,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_progress(
    session_id: str,
    iteration: int,
    max_iterations: int,
    message: str,
    quality_score: float | None = None,
) -> dict:
    """Emit a progress update event."""
    return {
        "event": EventType.PROGRESS.value,
        "data": json.dumps(
            {
                "type": EventType.PROGRESS.value,
                "session_id": session_id,
                "iteration": iteration,
                "max_iterations": max_iterations,
                "message": message,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_decision(
    session_id: str, decision: str, reasoning: str, next_action: str
) -> dict:
    """Emit a decision event from the critic."""
    return {
        "event": EventType.DECISION.value,
        "data": json.dumps(
            {
                "type": EventType.DECISION.value,
                "session_id": session_id,
                "decision": decision,
                "reasoning": reasoning,
                "next_action": next_action,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_retrieval(
    session_id: str,
    source: str,
    query: str,
    result_count: int,
    sample_results: list,
) -> dict:
    """Emit a retrieval event."""
    return {
        "event": EventType.RETRIEVAL.value,
        "data": json.dumps(
            {
                "type": EventType.RETRIEVAL.value,
                "session_id": session_id,
                "source": source,
                "query": query,
                "result_count": result_count,
                "sample_results": sample_results,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_insight(
    session_id: str,
    category: str,
    title: str,
    description: str,
    confidence: float,
) -> dict:
    """Emit an insight event."""
    return {
        "event": EventType.INSIGHT.value,
        "data": json.dumps(
            {
                "type": EventType.INSIGHT.value,
                "session_id": session_id,
                "category": category,
                "title": title,
                "description": description,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_output(
    session_id: str, format: str, content_preview: str, url: str | None = None
) -> dict:
    """Emit an output event."""
    return {
        "event": EventType.OUTPUT.value,
        "data": json.dumps(
            {
                "type": EventType.OUTPUT.value,
                "session_id": session_id,
                "format": format,
                "content_preview": content_preview,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


async def _emit_final_response(
    session_id: str,
    response: str,
    quality_score: float,
    iterations_used: int,
    sources_used: list[str],
) -> dict:
    """Emit the final response event."""
    return {
        "event": EventType.FINAL_RESPONSE.value,
        "data": json.dumps(
            {
                "type": EventType.FINAL_RESPONSE.value,
                "session_id": session_id,
                "response": response,
                "quality_score": quality_score,
                "iterations_used": iterations_used,
                "sources_used": sources_used,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


# =============================================================================
# Session Management Endpoints
# =============================================================================


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get the current state of a research session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "session_id": session.session_id,
        "query": session.query,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "final_response": session.final_response,
        "error": session.error,
    }


# =============================================================================
# Development Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7860,
        reload=settings.debug,
    )
