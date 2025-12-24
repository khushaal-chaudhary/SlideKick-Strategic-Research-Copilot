"""
Critic Node - Self-reflection and quality evaluation.

THIS IS WHAT MAKES THE SYSTEM TRULY AGENTIC.

The critic evaluates the quality of the analysis and decides:
1. Is the answer good enough? → Proceed to generation
2. Is something missing? → Loop back to retriever with refinement focus
3. Have we tried too many times? → Proceed anyway with caveats

This creates a genuine feedback loop, not just a linear pipeline.
"""

import json
import logging
from typing import Any

from copilot.agent.state import QueryType, RefinementType, ResearchState
from copilot.config.settings import settings
from copilot.llm import get_llm

logger = logging.getLogger(__name__)


CRITIC_PROMPT = """You are a research quality critic. Your job is to evaluate whether the analysis adequately answers the original query AND decide what to do next.

## Original Query
{query}

## Query Type
{query_type}

## Data Retrieved

### From Knowledge Graph ({graph_count} results):
{graph_summary}

### From Vector Search ({vector_count} results):
{vector_summary}

### From Web Search ({web_count} results):
{web_summary}

### AI-Generated Web Summary:
{web_ai_answer}

### From Financial Data ({financial_count} results):
{financial_summary}

## Current Analysis

### Entities Found ({entity_count}):
{entities}

### Key Insights ({insight_count}):
{insights}

### Synthesis:
{synthesis}

## Iteration Context
- Current iteration: {iteration} of {max_iterations}
- Previous refinement focus: {previous_focus}

## Evaluation Criteria:
1. **Completeness**: Does the analysis address all aspects of the query?
2. **Specificity**: Are there concrete facts/data, not just generalities?
3. **Relevance**: Is everything directly relevant to the query?
4. **Depth**: For strategic queries, are there actionable insights?
5. **Evidence**: Are claims supported by retrieved data?

## Available Tools for Refinement:
- **web_search**: Search the internet for current information, recent news, real-time data
- **vector_search**: Semantic search through documents for relevant passages and context
- **more_graph**: Deeper exploration of knowledge graph relationships
- **financial_data**: Get stock quotes, company fundamentals, financial metrics, earnings data
- **none**: No refinement needed, proceed to generate response

## Decision Guidelines:
- Use **web_search** when: Query needs current/recent info, news, real-time data, or graph lacks specifics
- Use **vector_search** when: Need more context, explanations, or detailed passages about a topic
- Use **more_graph** when: Entities exist but relationships are unclear
- Use **financial_data** when: Query involves stocks, P/E ratios, revenue, market cap, financial comparisons, or company fundamentals. Provide stock symbols (e.g., "MSFT,AAPL") in refinement_query.
- Use **none** when: Analysis is sufficient OR we've exhausted useful options OR we already have good results

## Your Tasks:
1. Score the quality (0.0 to 1.0)
2. Identify specific gaps that would improve the answer
3. Decide which tool to use (or none)
4. If using a tool, provide an optimized search query

## Response Format (JSON):
{{
    "quality_score": 0.75,
    "is_sufficient": false,
    "evaluation": {{
        "completeness": 0.8,
        "specificity": 0.6,
        "relevance": 0.9,
        "depth": 0.7,
        "evidence": 0.7
    }},
    "gaps_identified": [
        "Missing current information about X",
        "No concrete metrics found"
    ],
    "refinement_tool": "web_search|vector_search|more_graph|financial_data|none",
    "refinement_query": "Microsoft AI Copilot announcements December 2024",
    "reasoning": "The knowledge graph has good historical data but lacks recent announcements. Web search will provide current information."
}}

## Example for Financial Queries:
{{
    "quality_score": 0.4,
    "is_sufficient": false,
    "gaps_identified": ["Missing P/E ratio", "No revenue data", "Need stock price"],
    "refinement_tool": "financial_data",
    "refinement_query": "MSFT,AAPL",
    "reasoning": "Query asks about financial metrics but we have no financial data. Need to fetch from financial API."
}}

## Scoring Guidelines:
- 0.7+ is typically sufficient for simple factual queries
- 0.8+ is needed for strategic queries before proceeding
- If iteration is near max, consider proceeding with what we have

Respond with valid JSON only.
"""


def _format_insights(insights: list[dict]) -> str:
    """Format insights for the critic."""
    if not insights:
        return "No insights generated."
    
    formatted = []
    for i, insight in enumerate(insights, 1):
        formatted.append(
            f"{i}. [{insight.get('category', 'general')}] {insight.get('title', 'Untitled')}\n"
            f"   {insight.get('description', '')[:200]}"
        )
    return "\n".join(formatted)


def _format_graph_results(results: list[dict]) -> str:
    """Format graph results for the critic."""
    if not results:
        return "No results from knowledge graph."
    
    formatted = []
    for r in results[:10]:  # Limit to avoid token overflow
        if "entity" in r:
            formatted.append(f"- {r['entity']} ({r.get('types', [])})")
        elif "source" in r:
            formatted.append(f"- {r['source']} --[{r.get('relationship', '')}]--> {r.get('target', '')}")
    return "\n".join(formatted)


def _format_web_results(results: list[dict]) -> str:
    """Format web results for the critic."""
    if not results:
        return "No web search results."
    
    formatted = []
    for r in results[:5]:  # Limit to top 5
        title = r.get("title", "")[:60]
        snippet = r.get("snippet", "")[:100]
        formatted.append(f"- {title}: {snippet}...")
    return "\n".join(formatted)


def _format_vector_results(results: list[dict]) -> str:
    """Format vector search results for the critic."""
    if not results:
        return "No vector search results."

    formatted = []
    for r in results[:5]:  # Limit to top 5
        source = r.get("source", "unknown")
        score = r.get("score", 0)
        text = r.get("text", "")[:150]  # Short preview
        formatted.append(f"- [{source}] (score: {score:.2f}) {text}...")
    return "\n".join(formatted)


def _format_financial_results(results: list[dict]) -> str:
    """Format financial data results for the critic."""
    if not results:
        return "No financial data available."

    formatted = []
    for r in results:
        if "symbol" in r:
            symbol = r.get("symbol", "")
            parts = [f"**{symbol}**"]

            if "overview" in r:
                ov = r["overview"]
                parts.append(f"  - Name: {ov.get('name', 'N/A')}")
                parts.append(f"  - Sector: {ov.get('sector', 'N/A')}")
                parts.append(f"  - P/E Ratio: {ov.get('pe_ratio', 'N/A')}")
                parts.append(f"  - Market Cap: {ov.get('market_cap', 'N/A')}")
                parts.append(f"  - Profit Margin: {ov.get('profit_margin', 'N/A')}")

            if "quote" in r:
                q = r["quote"]
                parts.append(f"  - Price: ${q.get('price', 'N/A')}")
                parts.append(f"  - Change: {q.get('change_percent', 'N/A')}")

            if "income_statement" in r:
                inc = r["income_statement"]
                parts.append(f"  - Revenue: {inc.get('total_revenue', 'N/A')}")
                parts.append(f"  - Net Income: {inc.get('net_income', 'N/A')}")

            formatted.append("\n".join(parts))

        elif "news_sentiment" in r:
            news = r["news_sentiment"]
            formatted.append(f"**Recent News** ({len(news)} articles)")
            for article in news[:3]:
                formatted.append(f"  - [{article.get('sentiment', 'N/A')}] {article.get('title', '')[:60]}...")

    return "\n".join(formatted) if formatted else "No financial data available."


def _parse_critique_response(response: str) -> dict[str, Any]:
    """Parse the LLM's critique response."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse critique JSON: %s", e)
        # Optimistic fallback - proceed with generation
        return {
            "quality_score": 0.7,
            "is_sufficient": True,
            "gaps_identified": [],
            "refinement_tool": "none",
            "refinement_query": "",
            "reasoning": "Critique parsing failed, proceeding with available data",
        }


def critic_node(state: ResearchState) -> dict[str, Any]:
    """
    Critically evaluate the analysis quality AND decide next tool.
    
    This node:
    1. Evaluates completeness, specificity, relevance, depth, evidence
    2. Calculates an overall quality score
    3. Decides which tool to use next (web_search, more_graph, none)
    4. Provides optimized query for the chosen tool
    
    The decision to loop back vs proceed is made in the workflow routing,
    based on the `needs_refinement` flag this node sets.
    
    Returns:
        State updates with critique, refinement decision, and tool selection
    """
    query = state["original_query"]
    query_type = state.get("query_type", QueryType.UNKNOWN.value)
    entities = state.get("entities_found", [])
    insights = state.get("insights", [])
    synthesis = state.get("synthesis", "")
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", settings.max_iterations)
    previous_focus = state.get("refinement_focus", "")
    
    # Get retrieval results for context
    graph_results = state.get("graph_results", [])
    vector_results = state.get("vector_results", [])
    web_results = state.get("web_results", [])
    web_ai_answer = state.get("web_ai_answer", "")
    financial_results = state.get("financial_results", [])
    
    logger.info("🎯 Critic: Evaluating analysis quality (iteration %d/%d)...",
               iteration, max_iterations)
    logger.info("   Data available: graph=%d, vector=%d, web=%d, financial=%d, ai_answer=%s",
               len(graph_results), len(vector_results), len(web_results),
               len(financial_results), "yes" if web_ai_answer else "no")
    
    # Quick check: if we've hit max iterations, don't bother evaluating deeply
    if iteration >= max_iterations:
        logger.warning("   Max iterations reached, proceeding regardless of quality.")
        return {
            "critique": {
                "quality_score": state.get("quality_score", 0.5),
                "is_sufficient": True,  # Force proceed
                "gaps_identified": ["Max iterations reached"],
                "reasoning": "Proceeding due to iteration limit",
            },
            "quality_score": state.get("quality_score", 0.5),
            "needs_refinement": False,
            "refinement_type": RefinementType.NONE.value,
            "refinement_focus": "",
        }
    
    llm = get_llm(temperature=0)  # Deterministic for evaluation
    
    # Build the critique prompt with full context
    prompt = CRITIC_PROMPT.format(
        query=query,
        query_type=query_type,
        graph_count=len(graph_results),
        graph_summary=_format_graph_results(graph_results),
        vector_count=len(vector_results),
        vector_summary=_format_vector_results(vector_results),
        web_count=len(web_results),
        web_summary=_format_web_results(web_results),
        web_ai_answer=web_ai_answer if web_ai_answer else "No AI summary available.",
        financial_count=len(financial_results),
        financial_summary=_format_financial_results(financial_results),
        entity_count=len(entities),
        entities=", ".join(entities[:20]) or "None found",
        insight_count=len(insights),
        insights=_format_insights(insights),
        synthesis=synthesis[:1000] or "No synthesis generated",
        iteration=iteration,
        max_iterations=max_iterations,
        previous_focus=previous_focus or "None",
    )
    
    response = llm.invoke(prompt)
    critique = _parse_critique_response(response.content)
    
    # Extract key decisions
    quality_score = critique.get("quality_score", 0.5)
    is_sufficient = critique.get("is_sufficient", False)
    gaps = critique.get("gaps_identified", [])
    refinement_tool = critique.get("refinement_tool", "none")
    refinement_query = critique.get("refinement_query", "")
    
    # Map tool string to RefinementType enum
    tool_mapping = {
        "web_search": RefinementType.WEB_SEARCH.value,
        "vector_search": RefinementType.VECTOR_SEARCH.value,
        "more_graph": RefinementType.MORE_GRAPH.value,
        "financial_data": RefinementType.FINANCIAL_DATA.value,
        "none": RefinementType.NONE.value,
    }
    refinement_type = tool_mapping.get(refinement_tool, RefinementType.NONE.value)
    
    # Determine quality threshold based on query type
    threshold = settings.quality_threshold
    if query_type == QueryType.STRATEGIC.value:
        threshold = max(threshold, 0.8)  # Strategic queries need higher quality
    elif query_type == QueryType.FACTUAL.value:
        threshold = min(threshold, 0.7)  # Factual queries can proceed sooner
    elif query_type == QueryType.FINANCIAL.value:
        threshold = max(threshold, 0.75)  # Financial queries need accurate data
    
    # Make the refinement decision
    needs_refinement = (
        not is_sufficient 
        #and quality_score < threshold 
        and iteration < max_iterations
        and refinement_type != RefinementType.NONE.value  # Critic chose a tool
    )
    
    logger.info("   Quality score: %.2f (threshold: %.2f)", quality_score, threshold)
    logger.info("   Sufficient: %s, Needs refinement: %s", is_sufficient, needs_refinement)
    
    if gaps:
        logger.info("   Gaps: %s", ", ".join(gaps[:3]))
    
    if needs_refinement:
        logger.info("   → Tool: %s", refinement_type)
        logger.info("   → Query: %s", refinement_query[:50])
    
    # Build return state
    result = {
        "critique": critique,
        "quality_score": quality_score,
        "needs_refinement": needs_refinement,
        "refinement_type": refinement_type if needs_refinement else RefinementType.NONE.value,
        "refinement_focus": refinement_query if needs_refinement else "",
    }
    
    # CRITICAL: Increment iteration counter when looping back
    if needs_refinement:
        result["iteration"] = iteration + 1
        logger.info("   → Incrementing iteration to %d", iteration + 1)
    
    return result