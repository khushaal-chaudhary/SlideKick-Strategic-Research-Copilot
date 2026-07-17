"""
Agent nodes - Individual processing steps in the research workflow.

Each node is a function that:
1. Takes the current ResearchState
2. Performs its specific task
3. Returns a dict of state updates

The nodes form a graph where edges (including conditional edges)
determine the flow based on state values.
"""

from copilot.agent.nodes.analyzer import analyzer_node
from copilot.agent.nodes.critic import critic_node
from copilot.agent.nodes.generator import generator_node
from copilot.agent.nodes.planner import planner_node
from copilot.agent.nodes.responder import responder_node
from copilot.agent.nodes.retrieval import (
    financial_retrieval_node,
    graph_retrieval_node,
    rerank_node,
    vector_retrieval_node,
    web_retrieval_node,
)

__all__ = [
    "planner_node",
    "graph_retrieval_node",
    "vector_retrieval_node",
    "web_retrieval_node",
    "financial_retrieval_node",
    "rerank_node",
    "analyzer_node",
    "critic_node",
    "generator_node",
    "responder_node",
]
