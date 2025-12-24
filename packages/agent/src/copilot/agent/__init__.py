"""
Agent module - LangGraph orchestration.

The agent consists of:
- State: The data that flows through the graph
- Nodes: Processing steps (planner, retriever, analyzer, critic, generator, responder)
- Workflow: The graph structure with conditional edges
"""

from copilot.agent.state import (
    OutputFormat,
    QueryType,
    RefinementType,
    ResearchState,
    RetrievalStrategy,
    create_initial_state,
)
from copilot.agent.workflow import (
    ResearchCopilot,
    build_research_graph,
    compile_research_agent,
    create_copilot,
)

__all__ = [
    # State
    "ResearchState",
    "QueryType",
    "RetrievalStrategy",
    "RefinementType",
    "OutputFormat",
    "create_initial_state",
    # Workflow
    "build_research_graph",
    "compile_research_agent",
    "ResearchCopilot",
    "create_copilot",
]