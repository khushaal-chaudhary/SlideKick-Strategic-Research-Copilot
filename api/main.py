"""
SlideKick API - Strategic Research Copilot

FastAPI server for Hugging Face Spaces deployment.
Provides endpoints for the web interface to interact with the research agent.

Uses the real LangGraph agent with Groq LLM + Ollama fallback.
"""

import asyncio
import json
import logging
import os
import sys
import threading
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from queue import Queue, Empty

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

# Add agent package to path if running in Docker/HF Spaces
agent_path = os.path.join(os.path.dirname(__file__), "..", "packages", "agent", "src")
if os.path.exists(agent_path):
    sys.path.insert(0, agent_path)

# Try to import the real agent
try:
    from copilot.agent import create_copilot, ResearchState
    from copilot.llm import activate_fallback, set_provider_override
    AGENT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Agent not available, using demo mode: {e}")
    AGENT_AVAILABLE = False
    set_provider_override = None  # Dummy for type checking

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
    return HealthResponse(
        version=settings.api_version,
        model_loaded=AGENT_AVAILABLE,
    )


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
        llm_provider=request.llm_provider,
        status="pending",
    )
    sessions[session_id] = session

    logger.info(f"New query submitted: {session_id} - {request.query[:50]}... (provider={request.llm_provider.value})")

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
                "event": "message",
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
            # Real Agent Flow
            # =================================================================
            if AGENT_AVAILABLE:
                async for event in _run_real_agent(
                    session_id, session.query, session.llm_provider.value
                ):
                    yield event
            else:
                # Demo flow when agent is not available
                async for event in _run_demo_agent(session_id, session.query):
                    yield event

            # Complete event
            session.status = "completed"
            yield {
                "event": "message",
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
                "event": "message",
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
# Real Agent Execution
# =============================================================================


async def _run_real_agent(session_id: str, query: str, llm_provider: str = "ollama") -> AsyncGenerator[dict, None]:
    """
    Run the real LangGraph agent and yield SSE events in real-time.

    Uses a thread-safe queue to stream events as they're produced.

    Args:
        session_id: Unique session identifier
        query: The research question
        llm_provider: LLM provider to use ("ollama" or "groq")
    """
    session = sessions[session_id]
    event_queue: Queue = Queue()

    # Map LangGraph node names to our AgentNode enum
    node_mapping = {
        "planner": AgentNode.PLANNER,
        "retriever": AgentNode.RETRIEVER,
        "analyzer": AgentNode.ANALYZER,
        "critic": AgentNode.CRITIC,
        "generator": AgentNode.GENERATOR,
        "responder": AgentNode.RESPONDER,
    }

    def run_agent():
        """Run agent in background thread, pushing events to queue."""
        try:
            # Set the LLM provider override for this request
            if set_provider_override:
                set_provider_override(llm_provider)

            copilot = create_copilot()
            copilot.configure(max_iterations=settings.max_iterations)

            for event in copilot.stream(query, thread_id=session_id):
                event_queue.put(("event", event))

            event_queue.put(("done", None))

        except Exception as e:
            logger.error(f"Agent thread error: {e}")
            event_queue.put(("error", e))
        finally:
            # Clear the provider override after request
            if set_provider_override:
                set_provider_override(None)

    # Start agent in background thread
    agent_thread = threading.Thread(target=run_agent, daemon=True)
    agent_thread.start()

    # Process events as they arrive
    last_state = {}

    while True:
        # Non-blocking sleep to keep event loop responsive
        await asyncio.sleep(0.1)

        try:
            # Non-blocking queue check
            try:
                msg_type, payload = event_queue.get_nowait()
            except Empty:
                continue

            if msg_type == "done":
                break

            if msg_type == "error":
                raise payload

            # Process LangGraph event
            event = payload
            for node_name, state in event.items():
                if node_name not in node_mapping:
                    continue

                node = node_mapping[node_name]

                # Emit node start
                yield await _emit_node_event(
                    session_id,
                    node,
                    "start",
                    f"Processing {node_name}...",
                )

                # Extract relevant data from state and emit events
                if node_name == "planner":
                    entities = state.get("entities_of_interest", [])
                    entity_preview = ", ".join(entities[:3]) if entities else "none"
                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        f"Identified {len(entities)} entities: {entity_preview}",
                        {"entities": entities},
                    )

                elif node_name == "retriever":
                    graph_results = state.get("graph_results", [])
                    web_results = state.get("web_results", [])
                    financial_results = state.get("financial_results", [])

                    if graph_results:
                        yield await _emit_retrieval(
                            session_id,
                            "graph",
                            query,
                            len(graph_results),
                            graph_results[:3],
                        )

                    if web_results:
                        yield await _emit_retrieval(
                            session_id,
                            "web",
                            query,
                            len(web_results),
                            web_results[:3],
                        )

                    if financial_results:
                        yield await _emit_retrieval(
                            session_id,
                            "financial",
                            query,
                            len(financial_results),
                            financial_results[:3],
                        )

                    total = len(graph_results) + len(web_results) + len(financial_results)
                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        f"Retrieved {total} results (graph={len(graph_results)}, web={len(web_results)}, financial={len(financial_results)})",
                    )

                elif node_name == "analyzer":
                    insights = state.get("insights", [])
                    for insight in insights[:3]:
                        yield await _emit_insight(
                            session_id,
                            insight.get("category", "insight"),
                            insight.get("title", "Finding"),
                            insight.get("description", ""),
                            insight.get("confidence", 0.8),
                        )

                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        f"Generated {len(insights)} insights",
                    )

                elif node_name == "critic":
                    quality = state.get("quality_score", 0.0)
                    needs_refinement = state.get("needs_refinement", False)
                    refinement_type = state.get("refinement_type", "none")
                    iteration = state.get("iteration", 1)

                    decision = "sufficient" if not needs_refinement else "refine"
                    next_action = "Generate response" if not needs_refinement else f"Loop back ({refinement_type})"

                    yield await _emit_decision(
                        session_id,
                        decision,
                        f"Quality: {quality:.0%}, Iteration: {iteration}",
                        next_action,
                    )

                    yield await _emit_progress(
                        session_id,
                        iteration,
                        state.get("max_iterations", 3),
                        next_action,
                        quality,
                    )

                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        f"Quality: {quality:.0%}",
                        {"quality_score": quality},
                    )

                elif node_name == "generator":
                    content = state.get("output_content", "")
                    yield await _emit_output(
                        session_id,
                        state.get("output_format", "chat"),
                        content[:100] + "..." if len(content) > 100 else content,
                    )

                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        "Content generated",
                    )

                elif node_name == "responder":
                    final = state.get("final_response", "")
                    session.final_response = final

                    yield await _emit_final_response(
                        session_id,
                        final,
                        state.get("quality_score", 0.8),
                        state.get("iteration", 1),
                        ["knowledge_graph", "llm"],
                    )

                    yield await _emit_node_event(
                        session_id,
                        node,
                        "complete",
                        "Response delivered",
                    )

                # Update last state
                last_state.update(state)

        except Exception as e:
            logger.error(f"Error processing agent event: {e}")
            raise


async def _run_demo_agent(session_id: str, query: str) -> AsyncGenerator[dict, None]:
    """
    Run the demo agent flow (simulated).

    Used when the real agent is not available.
    """
    session = sessions[session_id]

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

*Note: This is a demo response. Deploy with a real LLM for actual research.*

*Sources: Microsoft Shareholder Letters 2020-2024*"""

    session.final_response = final_response

    yield await _emit_final_response(
        session_id,
        final_response,
        0.85,
        2,
        ["demo_mode"],
    )

    yield await _emit_node_event(
        session_id, AgentNode.RESPONDER, "complete", "Response delivered"
    )


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
        "event": "message",
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
        "event": "message",
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
        "event": "message",
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
        "event": "message",
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
        "event": "message",
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
        "event": "message",
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
        "event": "message",
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
# Diagnostic Endpoints
# =============================================================================


@app.get("/api/debug/neo4j")
async def debug_neo4j():
    """
    Diagnostic endpoint to check Neo4j connection, schema, and sample data.

    Returns schema info and sample nodes to help debug retrieval issues.
    """
    if not AGENT_AVAILABLE:
        return {"error": "Agent not available - cannot check Neo4j"}

    try:
        from copilot.graph.connection import graph_connection

        result = {
            "status": "connected",
            "schema": None,
            "node_labels": [],
            "relationship_types": [],
            "sample_nodes": [],
            "total_nodes": 0,
            "total_relationships": 0,
        }

        # Get schema
        try:
            result["schema"] = graph_connection.schema
        except Exception as e:
            result["schema_error"] = str(e)

        # Get node labels
        try:
            labels = graph_connection.query("CALL db.labels()")
            result["node_labels"] = [l["label"] for l in labels]
        except Exception as e:
            result["labels_error"] = str(e)

        # Get relationship types
        try:
            rels = graph_connection.query("CALL db.relationshipTypes()")
            result["relationship_types"] = [r["relationshipType"] for r in rels]
        except Exception as e:
            result["rels_error"] = str(e)

        # Count nodes
        try:
            count = graph_connection.query("MATCH (n) RETURN count(n) AS count")
            result["total_nodes"] = count[0]["count"] if count else 0
        except Exception as e:
            result["count_error"] = str(e)

        # Count relationships
        try:
            rel_count = graph_connection.query("MATCH ()-[r]->() RETURN count(r) AS count")
            result["total_relationships"] = rel_count[0]["count"] if rel_count else 0
        except Exception as e:
            result["rel_count_error"] = str(e)

        # Get sample nodes (first 5 with their properties)
        try:
            samples = graph_connection.query("""
                MATCH (n)
                RETURN labels(n) AS labels, keys(n) AS properties,
                       n.id AS id, n.name AS name, n.text AS text
                LIMIT 5
            """)
            result["sample_nodes"] = samples
        except Exception as e:
            result["sample_error"] = str(e)

        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
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
