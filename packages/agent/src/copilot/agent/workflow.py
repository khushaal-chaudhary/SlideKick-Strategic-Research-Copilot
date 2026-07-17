"""
LangGraph Workflow Construction.

This module builds the research agent graph with:
1. Nodes (processing steps)
2. Edges (connections between nodes)
3. Conditional edges (decision points)

The key innovation is the CRITIC LOOP - the agent can decide
to loop back for more research if the quality is insufficient.
The critic also decides WHICH TOOL to use (web search, more graph, etc.)
"""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from copilot.agent.nodes import (
    analyzer_node,
    critic_node,
    financial_retrieval_node,
    generator_node,
    graph_retrieval_node,
    planner_node,
    rerank_node,
    responder_node,
    vector_retrieval_node,
    web_retrieval_node,
)
from copilot.agent.state import RefinementType, ResearchState, RetrievalStrategy

logger = logging.getLogger(__name__)

RETRIEVAL_NODES = [
    "graph_retrieval",
    "vector_retrieval",
    "web_retrieval",
    "financial_retrieval",
]

# Which retrieval node executes each critic refinement request
REFINEMENT_TO_NODE = {
    RefinementType.WEB_SEARCH.value: "web_retrieval",
    RefinementType.VECTOR_SEARCH.value: "vector_retrieval",
    RefinementType.MORE_GRAPH.value: "graph_retrieval",
    RefinementType.FINANCIAL_DATA.value: "financial_retrieval",
}


# =============================================================================
# Decision Functions (Used by Conditional Edges)
# =============================================================================

def route_retrieval(state: ResearchState) -> list[str]:
    """
    First-pass retrieval fan-out based on the planner's strategy.

    Returning multiple node names makes LangGraph run them in PARALLEL;
    the reducers on the result lists merge their outputs.
    """
    strategy = state.get("retrieval_strategy", RetrievalStrategy.HYBRID.value)

    if strategy == RetrievalStrategy.FINANCIAL_FIRST.value:
        if state.get("stock_symbols"):
            targets = ["financial_retrieval", "graph_retrieval"]
        else:
            targets = ["graph_retrieval"]
    elif strategy == RetrievalStrategy.VECTOR_ONLY.value:
        targets = ["vector_retrieval"]
    elif strategy == RetrievalStrategy.WEB_ONLY.value:
        targets = ["web_retrieval"]
    elif strategy == RetrievalStrategy.GRAPH_ONLY.value:
        targets = ["graph_retrieval"]
    else:
        # HYBRID / GRAPH_THEN_WEB: graph + vector concurrently
        targets = ["graph_retrieval", "vector_retrieval"]

    logger.info("🔀 Retrieval fan-out: %s (strategy: %s)", targets, strategy)
    return targets


def should_continue_research(state: ResearchState) -> Literal["retrieve", "generator"]:
    """
    Decide whether to loop back for more research or proceed to generation.

    This is the KEY DECISION POINT that makes the system agentic.
    The Critic has already decided:
    - needs_refinement: True/False
    - refinement_type: which tool to use (web_search, more_graph, etc.)

    Returns:
        "retrieve" if we need more data (critic requested refinement)
        "generator" if we're ready to generate output
    """
    needs_refinement = state.get("needs_refinement", False)
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)
    refinement_type = state.get("refinement_type", "none")

    if needs_refinement and iteration < max_iterations:
        logger.info("🔄 Decision: Loop back for refinement (iteration %d, tool: %s)",
                   iteration, refinement_type)
        return "retrieve"
    else:
        if iteration >= max_iterations:
            logger.info("✅ Decision: Max iterations reached, proceeding to generation")
        else:
            logger.info("✅ Decision: Quality sufficient, proceeding to generation")
        return "generator"


def route_after_critic(state: ResearchState) -> list[str]:
    """Send the critic's refinement request to the matching retrieval node."""
    if should_continue_research(state) == "generator":
        return ["generator"]
    node = REFINEMENT_TO_NODE.get(state.get("refinement_type", ""), "graph_retrieval")
    return [node]


# =============================================================================
# Graph Construction
# =============================================================================

def build_research_graph() -> StateGraph:
    """
    Build the research agent workflow graph.

    Graph Structure (Simplified):

    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │    START                                                         │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────┐                                                     │
    │  │ PLANNER │ ─── Understand query, extract entities              │
    │  └────┬────┘                                                     │
    │       │  fan-out by strategy (parallel)                          │
    │   ┌───┴────┬─────────┬───────────┐                               │
    │   ▼        ▼         ▼           ▼                               │
    │ GRAPH   VECTOR      WEB      FINANCIAL   ◄── critic loops back   │
    │   │        │         │           │           to ONE of these     │
    │   └───┬────┴─────────┴───────────┘                               │
    │       ▼                                                          │
    │  ┌──────────┐                                                    │
    │  │ RERANKER │ ─── Cross-encoder scores merged results (fan-in)   │
    │  └────┬─────┘                                                    │
    │       ▼                                                          │
    │  ┌──────────┐                                                    │
    │  │ ANALYZER │ ─── Synthesize all retrieved data                  │
    │  └────┬─────┘                                                    │
    │       ▼                                                          │
    │  ┌─────────┐                                                     │
    │  │ CRITIC  │ ─── Evaluate quality & decide next tool             │
    │  └────┬────┘                                                     │
    │       ▼                                                          │
    │  Good enough? ── NO ──► back to the requested retrieval node     │
    │       │                                                          │
    │      YES                                                         │
    │       ▼                                                          │
    │  ┌───────────┐                                                   │
    │  │ GENERATOR │ ─── Create deliverable                            │
    │  └─────┬─────┘                                                   │
    │        ▼                                                         │
    │  ┌───────────┐                                                   │
    │  │ RESPONDER │ ─── Format final response                         │
    │  └─────┬─────┘                                                   │
    │        ▼                                                         │
    │       END                                                        │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘

    Returns:
        Configured StateGraph ready for compilation
    """
    # Create the graph with our state type
    workflow = StateGraph(ResearchState)

    # -------------------------------------------------------------------------
    # Add Nodes
    # -------------------------------------------------------------------------
    workflow.add_node("planner", planner_node)
    workflow.add_node("graph_retrieval", graph_retrieval_node)
    workflow.add_node("vector_retrieval", vector_retrieval_node)
    workflow.add_node("web_retrieval", web_retrieval_node)
    workflow.add_node("financial_retrieval", financial_retrieval_node)
    workflow.add_node("reranker", rerank_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("responder", responder_node)

    # -------------------------------------------------------------------------
    # Set Entry Point
    # -------------------------------------------------------------------------
    workflow.set_entry_point("planner")

    # -------------------------------------------------------------------------
    # Add Edges
    # -------------------------------------------------------------------------

    # Planner → retrieval fan-out (parallel nodes chosen by strategy)
    workflow.add_conditional_edges("planner", route_retrieval, RETRIEVAL_NODES)

    # Every retrieval node joins at the reranker (fan-in), then analysis
    for node_name in RETRIEVAL_NODES:
        workflow.add_edge(node_name, "reranker")
    workflow.add_edge("reranker", "analyzer")

    # Analyzer → Critic (always critique after analysis)
    workflow.add_edge("analyzer", "critic")

    # Critic → Decision: Loop back OR proceed to generator
    # THIS IS THE KEY AGENTIC DECISION POINT
    # The Critic has set:
    #   - needs_refinement: True/False
    #   - refinement_type: "web_search", "more_graph", "vector_search", or "none"
    #   - refinement_focus: optimized query for the tool
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        RETRIEVAL_NODES + ["generator"],
    )

    # Generator → Responder (always respond after generating)
    workflow.add_edge("generator", "responder")

    # Responder → END
    workflow.add_edge("responder", END)

    return workflow


def compile_research_agent(checkpointer=None):
    """
    Compile the research agent graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        Compiled agent ready for invocation
    """
    workflow = build_research_graph()

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)

    return workflow.compile()


# =============================================================================
# High-Level Agent Interface
# =============================================================================

class ResearchCopilot:
    """
    High-level interface for the Strategic Research Copilot.

    This class provides a clean API for running research queries
    through the LangGraph agent.
    """

    def __init__(self, checkpointer=None) -> None:
        """
        Initialize the copilot.

        Args:
            checkpointer: Optional checkpointer for conversation memory
        """
        self._graph = compile_research_agent(checkpointer)
        self._config: dict = {}

    def configure(
        self,
        max_iterations: int = 3,
        **kwargs,
    ) -> "ResearchCopilot":
        """
        Configure the copilot.

        Args:
            max_iterations: Maximum research iterations
            **kwargs: Additional configuration

        Returns:
            Self for chaining
        """
        self._config["max_iterations"] = max_iterations
        self._config.update(kwargs)
        return self

    def research(
        self,
        query: str,
        thread_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict:
        """
        Run a research query.

        Args:
            query: The research question
            thread_id: Optional thread ID for conversation memory
            workspace_id: Optional BYOD namespace to include in retrieval

        Returns:
            Final state dictionary with response
        """
        from copilot.agent.state import create_initial_state

        initial_state = create_initial_state(
            query=query,
            max_iterations=self._config.get("max_iterations", 3),
            workspace_id=workspace_id,
        )

        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        logger.info("🚀 Starting research: %s", query[:50])

        result = self._graph.invoke(initial_state, config=config)

        logger.info("✅ Research complete (quality: %.0f%%)",
                   result.get("quality_score", 0) * 100)

        return result

    def get_response(self, query: str) -> str:
        """
        Convenience method to get just the response text.

        Args:
            query: The research question

        Returns:
            The final response text
        """
        result = self.research(query)
        return result.get("final_response", "No response generated.")

    def stream(
        self,
        query: str,
        thread_id: str | None = None,
        workspace_id: str | None = None,
        stream_mode: str | list[str] = "updates",
    ):
        """
        Stream the research execution.

        Yields state updates as each node executes. With
        stream_mode=["updates", "messages"], LLM tokens are interleaved as
        ("messages", (chunk, metadata)) tuples for token-level streaming.

        Args:
            query: The research question
            thread_id: Optional thread ID
            workspace_id: Optional BYOD namespace to include in retrieval
            stream_mode: LangGraph stream mode(s)

        Yields:
            State updates from each node (tagged tuples when multiple modes)
        """
        from copilot.agent.state import create_initial_state

        initial_state = create_initial_state(
            query=query,
            max_iterations=self._config.get("max_iterations", 3),
            workspace_id=workspace_id,
        )

        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        yield from self._graph.stream(initial_state, config=config, stream_mode=stream_mode)


def create_copilot(checkpointer=None) -> ResearchCopilot:
    """
    Create a new Research Copilot instance.

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Configured ResearchCopilot
    """
    return ResearchCopilot(checkpointer=checkpointer)
