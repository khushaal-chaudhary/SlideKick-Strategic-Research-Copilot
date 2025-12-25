"""
API Request/Response Schemas.

Pydantic models for request validation and response serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class AgentNode(str, Enum):
    """Agent workflow nodes."""

    PLANNER = "planner"
    RETRIEVER = "retriever"
    ANALYZER = "analyzer"
    CRITIC = "critic"
    GENERATOR = "generator"
    RESPONDER = "responder"


class EventType(str, Enum):
    """Types of SSE events."""

    # Lifecycle events
    START = "start"
    COMPLETE = "complete"
    ERROR = "error"

    # Node events
    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"

    # Progress events
    PROGRESS = "progress"
    DECISION = "decision"

    # Data events
    RETRIEVAL = "retrieval"
    INSIGHT = "insight"

    # Output events
    OUTPUT = "output"
    FINAL_RESPONSE = "final_response"


class QueryType(str, Enum):
    """Types of research queries."""

    FACTUAL = "factual"
    COMPARATIVE = "comparative"
    STRATEGIC = "strategic"
    EXPLORATORY = "exploratory"
    FINANCIAL = "financial"
    UNKNOWN = "unknown"


class LLMProvider(str, Enum):
    """Available LLM providers."""

    OLLAMA = "ollama"
    GROQ = "groq"


# =============================================================================
# Request Models
# =============================================================================


class QueryRequest(BaseModel):
    """Request to submit a research query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The research question to process",
        examples=["How has Microsoft's AI strategy evolved from 2020 to 2024?"],
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum research iterations",
    )
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OLLAMA,
        description="LLM provider to use (ollama=local/free, groq=fast/rate-limited)",
    )


# =============================================================================
# Response Models
# =============================================================================


class QueryResponse(BaseModel):
    """Response after submitting a query."""

    session_id: str = Field(
        description="Unique session ID to track the query processing"
    )
    query: str = Field(description="The submitted query")
    status: str = Field(default="processing", description="Current status")
    stream_url: str = Field(description="SSE endpoint URL for real-time updates")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "slidekick"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_loaded: bool = True  # Will be set dynamically when real agent is integrated


class APIInfoResponse(BaseModel):
    """Root API information response."""

    name: str = "SlideKick API"
    version: str = "1.0.0"
    description: str = "Research that kicks! AI sidekick with knowledge graphs and self-reflection."
    author: str = "Khushaal Chaudhary"
    documentation: str = "/docs"


# =============================================================================
# SSE Event Models
# =============================================================================


class BaseEvent(BaseModel):
    """Base class for SSE events."""

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str


class NodeEvent(BaseEvent):
    """Event for node start/complete."""

    node: AgentNode
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProgressEvent(BaseEvent):
    """Progress update event."""

    iteration: int
    max_iterations: int
    message: str
    quality_score: float | None = None


class DecisionEvent(BaseEvent):
    """Agent decision event (e.g., critic loop)."""

    decision: str
    reasoning: str
    next_action: str


class RetrievalEvent(BaseEvent):
    """Data retrieval event."""

    source: str  # graph, web, vector, financial
    query: str
    result_count: int
    sample_results: list[dict[str, Any]] = Field(default_factory=list)


class InsightEvent(BaseEvent):
    """Analysis insight event."""

    category: str
    title: str
    description: str
    confidence: float


class OutputEvent(BaseEvent):
    """Output generation event."""

    format: str
    content_preview: str
    url: str | None = None


class FinalResponseEvent(BaseEvent):
    """Final response event."""

    response: str
    quality_score: float
    iterations_used: int
    sources_used: list[str]


class ErrorEvent(BaseEvent):
    """Error event."""

    error: str
    details: str | None = None


# =============================================================================
# Session State (for tracking active sessions)
# =============================================================================


class SessionState(BaseModel):
    """State of an active research session."""

    session_id: str
    query: str
    llm_provider: LLMProvider = LLMProvider.OLLAMA
    status: str = "pending"  # pending, processing, completed, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    iteration: int = 0
    current_node: AgentNode | None = None
    events: list[BaseEvent] = Field(default_factory=list)
    final_response: str | None = None
    error: str | None = None
