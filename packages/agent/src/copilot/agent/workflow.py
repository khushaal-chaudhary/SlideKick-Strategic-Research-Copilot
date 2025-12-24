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
    generator_node,
    planner_node,
    responder_node,
    retriever_node,
)
from copilot.agent.state import ResearchState

logger = logging.getLogger(__name__)


# =============================================================================
# Decision Functions (Used by Conditional Edges)
# =============================================================================

def should_continue_research(state: ResearchState) -> Literal["retriever", "generator"]:
    """
    Decide whether to loop back for more research or proceed to generation.
    
    This is the KEY DECISION POINT that makes the system agentic.
    The Critic has already decided:
    - needs_refinement: True/False
    - refinement_type: which tool to use (web_search, more_graph, etc.)
    
    Returns:
        "retriever" if we need more data (critic requested refinement)
        "generator" if we're ready to generate output
    """
    needs_refinement = state.get("needs_refinement", False)
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)
    refinement_type = state.get("refinement_type", "none")
    
    if needs_refinement and iteration < max_iterations:
        logger.info("🔄 Decision: Loop back for refinement (iteration %d, tool: %s)", 
                   iteration, refinement_type)
        return "retriever"
    else:
        if iteration >= max_iterations:
            logger.info("✅ Decision: Max iterations reached, proceeding to generation")
        else:
            logger.info("✅ Decision: Quality sufficient, proceeding to generation")
        return "generator"


# =============================================================================
# Graph Construction
# =============================================================================

def build_research_graph() -> StateGraph:
    """
    Build the research agent workflow graph.
    
    Graph Structure (Simplified):
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │    START                                                         │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────┐                                                     │
    │  │ PLANNER │ ─── Understand query, extract entities              │
    │  └────┬────┘                                                     │
    │       │                                                          │
    │       ▼                                                          │
    │  ┌───────────┐                                                   │
    │  │ RETRIEVER │ ◄─────────────────────────────────────┐          │
    │  └─────┬─────┘   Executes tool requested by Critic   │          │
    │        │         (graph, web_search, vector, etc.)   │          │
    │        │                                              │          │
    │        ▼                                              │          │
    │  ┌──────────┐                                         │          │
    │  │ ANALYZER │ ─── Synthesize all retrieved data       │          │
    │  └────┬─────┘                                         │          │
    │       │                                               │          │
    │       ▼                                               │          │
    │  ┌─────────┐                                          │          │
    │  │ CRITIC  │ ─── Evaluate quality & decide next tool  │          │
    │  └────┬────┘                                          │          │
    │       │                                               │          │
    │       ▼                                               │          │
    │  ┌─────────────┐                                      │          │
    │  │ Good enough?│                                      │          │
    │  └──────┬──────┘                                      │          │
    │         │                                             │          │
    │   ┌─────┴─────┐                                       │          │
    │   │           │                                       │          │
    │  YES         NO ──────────────────────────────────────┘          │
    │   │         (Loop back with refinement_type set)                 │
    │   │                                                              │
    │   ▼                                                              │
    │  ┌───────────┐                                                   │
    │  │ GENERATOR │ ─── Create deliverable                            │
    │  └─────┬─────┘                                                   │
    │        │                                                         │
    │        ▼                                                         │
    │  ┌───────────┐                                                   │
    │  │ RESPONDER │ ─── Format final response                         │
    │  └─────┬─────┘                                                   │
    │        │                                                         │
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
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("responder", responder_node)
    
    # -------------------------------------------------------------------------
    # Set Entry Point
    # -------------------------------------------------------------------------
    workflow.set_entry_point("planner")
    
    # -------------------------------------------------------------------------
    # Add Edges (Simplified - no multi-step research plan)
    # -------------------------------------------------------------------------
    
    # Planner → Retriever (start retrieving after planning)
    workflow.add_edge("planner", "retriever")
    
    # Retriever → Analyzer (always analyze after retrieval)
    workflow.add_edge("retriever", "analyzer")
    
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
        should_continue_research,
        {
            "retriever": "retriever",  # Need more data (LOOP!)
            "generator": "generator",  # Quality sufficient
        },
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
    ) -> dict:
        """
        Run a research query.
        
        Args:
            query: The research question
            thread_id: Optional thread ID for conversation memory
            
        Returns:
            Final state dictionary with response
        """
        from copilot.agent.state import create_initial_state
        
        initial_state = create_initial_state(
            query=query,
            max_iterations=self._config.get("max_iterations", 3),
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
    
    def stream(self, query: str, thread_id: str | None = None):
        """
        Stream the research execution.
        
        Yields state updates as each node executes.
        
        Args:
            query: The research question
            thread_id: Optional thread ID
            
        Yields:
            State updates from each node
        """
        from copilot.agent.state import create_initial_state
        
        initial_state = create_initial_state(
            query=query,
            max_iterations=self._config.get("max_iterations", 3),
        )
        
        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}
        
        for event in self._graph.stream(initial_state, config=config):
            yield event


def create_copilot(checkpointer=None) -> ResearchCopilot:
    """
    Create a new Research Copilot instance.
    
    Args:
        checkpointer: Optional checkpointer for state persistence
        
    Returns:
        Configured ResearchCopilot
    """
    return ResearchCopilot(checkpointer=checkpointer)