"""
Research Agent State Definition.

This is the heart of the agentic system. The state flows through all nodes
and accumulates information as the agent researches, analyzes, and iterates.

Key Design Decisions:
1. research_plan: Allows the agent to decompose complex queries into steps
2. quality_score + needs_refinement: Enables the critic loop
3. retrieval_strategy: Records decisions for observability
4. iteration tracking: Prevents infinite loops
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class QueryType(str, Enum):
    """Classification of research query types."""

    FACTUAL = "factual"              # "What products did X launch?"
    COMPARATIVE = "comparative"       # "How does X compare to Y?"
    STRATEGIC = "strategic"           # "How should we respond to X?"
    EXPLORATORY = "exploratory"       # "What are the key themes in X?"
    FINANCIAL = "financial"           # "What is MSFT's P/E ratio?", "Compare AAPL vs GOOGL revenue"
    UNKNOWN = "unknown"


class RetrievalStrategy(str, Enum):
    """Strategies for data retrieval."""

    GRAPH_ONLY = "graph_only"         # Just query the knowledge graph
    VECTOR_ONLY = "vector_only"       # Just semantic search
    HYBRID = "hybrid"                 # Graph + vector
    GRAPH_THEN_WEB = "graph_then_web" # Graph first, web if insufficient
    WEB_ONLY = "web_only"             # External search only
    FINANCIAL_FIRST = "financial_first"  # Start with financial data API for stock/company queries


class OutputFormat(str, Enum):
    """Desired output format."""
    
    CHAT = "chat"                     # Conversational response
    SLIDES = "slides"                 # Google Slides presentation
    DOCUMENT = "document"             # Long-form document
    BULLET_SUMMARY = "bullet_summary" # Structured bullet points


class RefinementType(str, Enum):
    """Types of refinement the critic can request."""

    NONE = "none"                     # No refinement needed
    WEB_SEARCH = "web_search"         # Search the internet for current info
    VECTOR_SEARCH = "vector_search"   # Semantic search in documents
    MORE_GRAPH = "more_graph"         # Deeper graph exploration
    FINANCIAL_DATA = "financial_data" # Get financial metrics, stock data, company fundamentals
    CLARIFY_QUERY = "clarify_query"   # Need to ask user for clarification


@dataclass
class ResearchStep:
    """A single step in the research plan."""
    
    description: str
    query: str                        # The specific query for this step
    status: str = "pending"           # pending, completed, failed
    results: list[dict] = field(default_factory=list)


@dataclass
class RetrievalResult:
    """Results from a retrieval operation."""
    
    source: str                       # "graph", "vector", "web"
    query: str                        # The query that was executed
    results: list[dict[str, Any]]     # Raw results
    result_count: int = 0
    confidence: float = 0.0           # How confident are we in these results?


@dataclass 
class AnalysisInsight:
    """An insight extracted during analysis."""
    
    category: str                     # e.g., "competitive_gap", "strategic_theme"
    title: str
    description: str
    supporting_evidence: list[str]
    confidence: float


@dataclass
class CritiqueResult:
    """Results from the critic's evaluation."""
    
    quality_score: float              # 0.0 to 1.0
    is_sufficient: bool               # Does it meet the threshold?
    gaps_identified: list[str]        # What's missing?
    suggested_refinements: list[str]  # How to improve?
    reasoning: str                    # Why this score?


# =============================================================================
# Main State Definition (TypedDict for LangGraph)
# =============================================================================

class ResearchState(TypedDict, total=False):
    """
    The state that flows through the research agent.
    
    This TypedDict is used by LangGraph to manage state across nodes.
    All fields are optional (total=False) to allow partial updates.
    """
    
    # -------------------------------------------------------------------------
    # Conversation
    # -------------------------------------------------------------------------
    messages: Annotated[list[BaseMessage], add_messages]
    
    # -------------------------------------------------------------------------
    # Query Understanding
    # -------------------------------------------------------------------------
    original_query: str               # The user's original question
    query_type: str                   # QueryType value
    entities_of_interest: list[str]   # Extracted entities to focus on (full names for graph)
    stock_symbols: list[str]          # Stock ticker symbols for financial API (MSFT, AAPL)
    
    # -------------------------------------------------------------------------
    # Planning
    # -------------------------------------------------------------------------
    research_plan: list[dict]         # List of ResearchStep as dicts
    current_step_index: int           # Which step are we on?
    retrieval_strategy: str           # RetrievalStrategy value
    
    # -------------------------------------------------------------------------
    # Retrieval Results
    # -------------------------------------------------------------------------
    graph_results: list[dict]         # Results from Neo4j
    vector_results: list[dict]        # Results from vector search
    web_results: list[dict]           # Results from web search
    web_ai_answer: str                # AI-generated summary from Tavily
    financial_results: list[dict]     # Results from Alpha Vantage financial API
    all_retrievals: list[dict]        # All RetrievalResult as dicts
    
    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------
    insights: list[dict]              # List of AnalysisInsight as dicts
    synthesis: str                    # Synthesized analysis text
    entities_found: list[str]         # Entities discovered
    relationships_found: list[dict]   # Relationships discovered
    
    # -------------------------------------------------------------------------
    # Critique (Self-Reflection)
    # -------------------------------------------------------------------------
    critique: dict | None             # CritiqueResult as dict
    quality_score: float              # Current quality assessment
    needs_refinement: bool            # Should we loop back?
    refinement_type: str              # RefinementType - which tool to use
    refinement_focus: str             # What to focus on if refining
    
    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------
    output_format: str                # OutputFormat value
    output_content: str               # Generated content
    output_url: str | None            # URL if slides/doc generated
    final_response: str               # Response to user

    # -------------------------------------------------------------------------
    # Slides Sharing
    # -------------------------------------------------------------------------
    user_share_email: str | None      # Email to share slides with (user-provided)
    
    # -------------------------------------------------------------------------
    # Control Flow
    # -------------------------------------------------------------------------
    iteration: int                    # Current iteration count
    max_iterations: int               # Maximum allowed iterations
    error: str | None                 # Error message if failed
    

# =============================================================================
# State Factory Functions
# =============================================================================

def create_initial_state(query: str, max_iterations: int = 3) -> ResearchState:
    """
    Create the initial state for a new research query.
    
    Args:
        query: The user's research question
        max_iterations: Maximum research loops allowed
        
    Returns:
        Initial ResearchState ready for processing
    """
    return ResearchState(
        messages=[],
        original_query=query,
        query_type=QueryType.UNKNOWN.value,
        entities_of_interest=[],
        stock_symbols=[],
        research_plan=[],
        current_step_index=0,
        retrieval_strategy=RetrievalStrategy.HYBRID.value,
        graph_results=[],
        vector_results=[],
        web_results=[],
        web_ai_answer="",
        financial_results=[],
        all_retrievals=[],
        insights=[],
        synthesis="",
        entities_found=[],
        relationships_found=[],
        critique=None,
        quality_score=0.0,
        needs_refinement=False,
        refinement_type=RefinementType.NONE.value,
        refinement_focus="",
        output_format=OutputFormat.CHAT.value,
        output_content="",
        output_url=None,
        slides_content=None,
        user_share_email=None,
        final_response="",
        iteration=0,
        max_iterations=max_iterations,
        error=None,
    )


def state_summary(state: ResearchState) -> str:
    """
    Generate a human-readable summary of the current state.
    
    Useful for debugging and LangSmith traces.
    """
    return f"""
Research State Summary:
━━━━━━━━━━━━━━━━━━━━━━━
Query: {state.get('original_query', 'N/A')[:50]}...
Type: {state.get('query_type', 'unknown')}
Iteration: {state.get('iteration', 0)}/{state.get('max_iterations', 3)}

Plan: {len(state.get('research_plan', []))} steps
Current Step: {state.get('current_step_index', 0)}
Strategy: {state.get('retrieval_strategy', 'N/A')}

Results:
  - Graph: {len(state.get('graph_results', []))} items
  - Vector: {len(state.get('vector_results', []))} items
  - Web: {len(state.get('web_results', []))} items
  - Financial: {len(state.get('financial_results', []))} items

Analysis:
  - Insights: {len(state.get('insights', []))}
  - Entities: {len(state.get('entities_found', []))}

Quality: {state.get('quality_score', 0):.2f}
Needs Refinement: {state.get('needs_refinement', False)}
Refinement Type: {state.get('refinement_type', 'none')}
Output Format: {state.get('output_format', 'chat')}
"""