"""
Planner Node - Decomposes research queries into executable steps.

This is where the agent becomes "agentic" - it doesn't just answer,
it PLANS how to answer. This enables multi-step research.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage

from copilot.agent.state import (
    OutputFormat,
    QueryType,
    ResearchState,
    RetrievalStrategy,
)
from copilot.llm import get_llm

logger = logging.getLogger(__name__)


PLANNER_PROMPT = """You are a strategic research planner. Your job is to analyze a research query and create an execution plan.

## Your Tasks:
1. Classify the query type
2. Extract key entities to research (including stock ticker symbols)
3. Decide the best retrieval strategy
4. Create a step-by-step research plan
5. Determine the appropriate output format

## Query Types:
- factual: Simple fact lookup ("What products did X launch?")
- comparative: Comparing entities ("How does X compare to Y?")
- strategic: Requires synthesis and recommendations ("How should we respond to X?")
- exploratory: Open-ended discovery ("What are the key themes?")
- financial: Stock/company financial analysis ("What is MSFT's P/E ratio?", "Compare AAPL vs GOOGL revenue", "Is Tesla overvalued?")

## Retrieval Strategies:
- graph_only: Query is about known entities and relationships
- hybrid: Need both structured (graph) and semantic (vector) search
- graph_then_web: Start with graph, supplement with web if sparse
- financial_first: Query involves stocks, financial metrics, or company fundamentals - start with financial data API

## Output Formats:
- chat: Conversational response (simple questions)
- slides: Presentation (strategic/executive questions)
- bullet_summary: Structured list (comparative questions)

## Entity Extraction Guidelines:
- For financial queries, extract stock ticker symbols in UPPERCASE (e.g., MSFT, AAPL, TSLA, GOOGL, AMZN)
- Recognize company names and map to tickers when possible (Microsoft → MSFT, Apple → AAPL)
- Extract financial metrics mentioned: revenue, profit margin, P/E ratio, EPS, market cap, etc.

## Research Query:
{query}

## Response Format (JSON):
{{
    "query_type": "factual|comparative|strategic|exploratory|financial",
    "entities_of_interest": ["MSFT", "AAPL", "entity1"],
    "retrieval_strategy": "graph_only|hybrid|graph_then_web|financial_first",
    "output_format": "chat|slides|bullet_summary",
    "research_plan": [
        {{
            "step": 1,
            "description": "What this step accomplishes",
            "query": "Specific query for this step"
        }}
    ],
    "reasoning": "Brief explanation of your planning decisions"
}}

## Examples:

Query: "What is Microsoft's P/E ratio and how does it compare to Apple?"
Response:
{{
    "query_type": "financial",
    "entities_of_interest": ["MSFT", "AAPL"],
    "retrieval_strategy": "financial_first",
    "output_format": "chat",
    "research_plan": [
        {{"step": 1, "description": "Get financial metrics for MSFT and AAPL", "query": "P/E ratio comparison MSFT AAPL"}}
    ],
    "reasoning": "Financial comparison query - need P/E ratios from financial API"
}}

Query: "Analyze Tesla's financial health and stock performance"
Response:
{{
    "query_type": "financial",
    "entities_of_interest": ["TSLA"],
    "retrieval_strategy": "financial_first",
    "output_format": "bullet_summary",
    "research_plan": [
        {{"step": 1, "description": "Get Tesla company overview and fundamentals", "query": "TSLA company overview"}},
        {{"step": 2, "description": "Get income statement and profitability metrics", "query": "TSLA financial statements"}},
        {{"step": 3, "description": "Get current stock quote and performance", "query": "TSLA stock price performance"}}
    ],
    "reasoning": "Comprehensive financial analysis - need fundamentals, financials, and stock data"
}}

Respond with valid JSON only, no markdown formatting.
"""


def _parse_plan_response(response: str) -> dict[str, Any]:
    """Parse the LLM's planning response."""
    # Clean up response (remove markdown code blocks if present)
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse plan JSON: %s", e)
        # Return a default plan
        return {
            "query_type": QueryType.UNKNOWN.value,
            "entities_of_interest": [],
            "retrieval_strategy": RetrievalStrategy.HYBRID.value,
            "output_format": OutputFormat.CHAT.value,
            "research_plan": [
                {
                    "step": 1,
                    "description": "Direct search for relevant information",
                    "query": "",  # Will use original query
                }
            ],
            "reasoning": "Fallback plan due to parsing error",
        }


def planner_node(state: ResearchState) -> dict[str, Any]:
    """
    Plan the research approach.
    
    This node:
    1. Analyzes the user's query
    2. Classifies the query type
    3. Extracts entities of interest
    4. Decides retrieval strategy
    5. Creates a multi-step research plan
    6. Determines output format
    
    Returns:
        State updates with the research plan
    """
    query = state["original_query"]
    logger.info("📋 Planner: Analyzing query and creating research plan...")
    
    llm = get_llm(temperature=0)  # Deterministic for planning
    
    # Generate the plan
    prompt = PLANNER_PROMPT.format(query=query)
    response = llm.invoke(prompt)
    
    # Parse the response
    plan_data = _parse_plan_response(response.content)
    
    # Validate and normalize
    query_type = plan_data.get("query_type", QueryType.UNKNOWN.value)
    if query_type not in [qt.value for qt in QueryType]:
        query_type = QueryType.UNKNOWN.value
        
    retrieval_strategy = plan_data.get("retrieval_strategy", RetrievalStrategy.HYBRID.value)
    if retrieval_strategy not in [rs.value for rs in RetrievalStrategy]:
        retrieval_strategy = RetrievalStrategy.HYBRID.value
        
    output_format = plan_data.get("output_format", OutputFormat.CHAT.value)
    if output_format not in [of.value for of in OutputFormat]:
        output_format = OutputFormat.CHAT.value
    
    # Build research steps
    research_plan = []
    for step in plan_data.get("research_plan", []):
        research_plan.append({
            "description": step.get("description", ""),
            "query": step.get("query", query),  # Fall back to original query
            "status": "pending",
            "results": [],
        })
    
    # Ensure at least one step
    if not research_plan:
        research_plan.append({
            "description": "Search for relevant information",
            "query": query,
            "status": "pending",
            "results": [],
        })
    
    logger.info("   Query type: %s", query_type)
    logger.info("   Strategy: %s", retrieval_strategy)
    logger.info("   Output format: %s", output_format)
    logger.info("   Research steps: %d", len(research_plan))
    
    return {
        "query_type": query_type,
        "entities_of_interest": plan_data.get("entities_of_interest", []),
        "retrieval_strategy": retrieval_strategy,
        "output_format": output_format,
        "research_plan": research_plan,
        "current_step_index": 0,
        "iteration": state.get("iteration", 0) + 1,
        "messages": [HumanMessage(content=query)],
    }