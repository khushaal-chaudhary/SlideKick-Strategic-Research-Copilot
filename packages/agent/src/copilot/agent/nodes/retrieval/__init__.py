"""
Retrieval nodes — one per data source so LangGraph can fan them out in
parallel with Send, plus a cross-encoder reranker as the fan-in.

The Critic decides WHAT tool to use. These nodes just EXECUTE.
"""

from copilot.agent.nodes.retrieval.financial import (
    _query_financial_data,
    financial_retrieval_node,
)
from copilot.agent.nodes.retrieval.graph import _query_graph, graph_retrieval_node
from copilot.agent.nodes.retrieval.reranker import rerank_node
from copilot.agent.nodes.retrieval.vector import _query_vector, vector_retrieval_node
from copilot.agent.nodes.retrieval.web import _query_web_tavily, web_retrieval_node

__all__ = [
    "_query_financial_data",
    "_query_graph",
    "_query_vector",
    "_query_web_tavily",
    "financial_retrieval_node",
    "graph_retrieval_node",
    "rerank_node",
    "vector_retrieval_node",
    "web_retrieval_node",
]
