"""
Analyzer Node - Synthesizes insights from retrieved data.

This node transforms raw data into structured insights
that can be critiqued and then used for generation.
"""

import json
import logging
from typing import Any

from copilot.agent.state import QueryType, ResearchState
from copilot.llm import get_llm

logger = logging.getLogger(__name__)


ANALYZER_PROMPT = """You are a strategic analyst synthesizing research findings.

## Research Query
{query}

## Query Type
{query_type}

## Retrieved Data

### From Knowledge Graph:
{graph_data}

### From Vector Search:
{vector_data}

### From Web Search:
{web_data}

### AI-Generated Web Summary (from Tavily):
{web_ai_summary}

### From Financial Data API:
{financial_data}

## Your Tasks:
1. Identify key entities mentioned in the data
2. Extract meaningful insights relevant to the query
3. Identify relationships and patterns
4. Note any gaps in the information
5. Synthesize a coherent analysis (use the AI summary as a starting point if available)

## Response Format (JSON):
{{
    "entities_found": ["entity1", "entity2"],
    "relationships_found": [
        {{"source": "entity1", "type": "RELATES_TO", "target": "entity2"}}
    ],
    "insights": [
        {{
            "category": "strategic_theme|competitive_gap|risk|opportunity|financial_metric|valuation|growth|profitability",
            "title": "Brief title",
            "description": "Detailed description",
            "supporting_evidence": ["evidence1", "evidence2"],
            "confidence": 0.8
        }}
    ],
    "gaps_identified": ["What information is missing"],
    "synthesis": "A 2-3 paragraph synthesis of the findings addressing the original query"
}}

Respond with valid JSON only.
"""


def _format_results(results: list[dict], max_items: int = 20) -> str:
    """Format results for the prompt."""
    if not results:
        return "No data retrieved."
    
    formatted = []
    for item in results[:max_items]:
        # Handle different result formats
        if "entity" in item:
            # Knowledge graph entity
            formatted.append(f"- Entity: {item['entity']} (Types: {item.get('types', [])})")
            if item.get("relationships"):
                for rel in item["relationships"][:3]:
                    formatted.append(f"  → {rel.get('rel', '?')}: {rel.get('target', '?')}")
        elif "source" in item and "target" in item and "relationship" in item:
            # Knowledge graph relationship
            formatted.append(
                f"- {item['source']} --[{item.get('relationship', '?')}]--> {item['target']}"
            )
        elif "text" in item and "score" in item and "source_type" in item:
            # Vector search result (semantic passage)
            source = item.get("source", "unknown")
            score = item.get("score", 0)
            text = item.get("text", "")[:600]  # Longer for context
            formatted.append(f"- [Document: {source}] (similarity: {score:.2f})")
            formatted.append(f"  \"{text}\"")
        elif "title" in item and ("content" in item or "snippet" in item):
            # Web search result (Tavily or DuckDuckGo)
            title = item.get("title", "")[:80]
            # Tavily uses 'content', DuckDuckGo uses 'snippet'
            content = item.get("content", item.get("snippet", ""))[:500]
            url = item.get("url", "")
            score = item.get("score", "")
            score_str = f" (relevance: {score:.2f})" if score else ""
            formatted.append(f"- [{title}]({url}){score_str}")
            formatted.append(f"  {content}")
        else:
            # Generic format
            formatted.append(f"- {json.dumps(item)[:200]}")
    
    if len(results) > max_items:
        formatted.append(f"... and {len(results) - max_items} more items")

    return "\n".join(formatted)


def _format_financial_results(results: list[dict]) -> str:
    """Format financial data results for the analyzer."""
    if not results:
        return "No financial data retrieved."

    formatted = []
    for r in results:
        if "symbol" in r:
            symbol = r.get("symbol", "")
            parts = [f"## {symbol}"]

            if "overview" in r:
                ov = r["overview"]
                parts.append("### Company Overview")
                parts.append(f"- Name: {ov.get('name', 'N/A')}")
                parts.append(f"- Sector: {ov.get('sector', 'N/A')}")
                parts.append(f"- Industry: {ov.get('industry', 'N/A')}")
                parts.append(f"- Description: {ov.get('description', 'N/A')[:300]}...")
                parts.append(f"- Market Cap: {ov.get('market_cap', 'N/A')}")
                parts.append(f"- P/E Ratio: {ov.get('pe_ratio', 'N/A')}")
                parts.append(f"- EPS: {ov.get('eps', 'N/A')}")
                parts.append(f"- Dividend Yield: {ov.get('dividend_yield', 'N/A')}")
                parts.append(f"- Profit Margin: {ov.get('profit_margin', 'N/A')}")
                parts.append(f"- 52 Week High: {ov.get('52_week_high', 'N/A')}")
                parts.append(f"- 52 Week Low: {ov.get('52_week_low', 'N/A')}")

            if "quote" in r:
                q = r["quote"]
                parts.append("### Stock Quote")
                parts.append(f"- Current Price: ${q.get('price', 'N/A')}")
                parts.append(f"- Change: {q.get('change', 'N/A')}")
                parts.append(f"- Change %: {q.get('change_percent', 'N/A')}")
                parts.append(f"- Volume: {q.get('volume', 'N/A')}")
                parts.append(f"- Latest Trading Day: {q.get('latest_trading_day', 'N/A')}")

            if "income_statement" in r:
                inc = r["income_statement"]
                parts.append("### Income Statement (Latest)")
                parts.append(f"- Total Revenue: {inc.get('total_revenue', 'N/A')}")
                parts.append(f"- Gross Profit: {inc.get('gross_profit', 'N/A')}")
                parts.append(f"- Operating Income: {inc.get('operating_income', 'N/A')}")
                parts.append(f"- Net Income: {inc.get('net_income', 'N/A')}")
                parts.append(f"- EBITDA: {inc.get('ebitda', 'N/A')}")

            formatted.append("\n".join(parts))

        elif "news_sentiment" in r:
            news = r["news_sentiment"]
            parts = ["## Recent News & Sentiment"]
            for article in news[:5]:
                sentiment = article.get("sentiment", "N/A")
                title = article.get("title", "")[:80]
                source = article.get("source", "Unknown")
                parts.append(f"- [{sentiment}] {title} ({source})")
            formatted.append("\n".join(parts))

    return "\n\n".join(formatted) if formatted else "No financial data retrieved."


def _parse_analysis_response(response: str) -> dict[str, Any]:
    """Parse the LLM's analysis response."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse analysis JSON: %s", e)
        return {
            "entities_found": [],
            "relationships_found": [],
            "insights": [],
            "gaps_identified": ["Analysis parsing failed"],
            "synthesis": response[:500],  # Use raw response as fallback
        }


def analyzer_node(state: ResearchState) -> dict[str, Any]:
    """
    Analyze and synthesize retrieved data.
    
    This node:
    1. Aggregates all retrieved data
    2. Extracts entities and relationships
    3. Generates insights relevant to the query type
    4. Creates a synthesis addressing the original query
    5. Leverages Tavily's AI summary when available
    
    Returns:
        State updates with analysis results
    """
    query = state["original_query"]
    query_type = state.get("query_type", QueryType.UNKNOWN.value)
    graph_results = state.get("graph_results", [])
    vector_results = state.get("vector_results", [])
    web_results = state.get("web_results", [])
    web_ai_answer = state.get("web_ai_answer", "")
    financial_results = state.get("financial_results", [])

    total_results = len(graph_results) + len(vector_results) + len(web_results) + len(financial_results)
    logger.info("🧠 Analyzer: Synthesizing %d results...", total_results)
    
    if web_ai_answer:
        logger.info("   📝 Tavily AI summary available (%d chars)", len(web_ai_answer))

    if financial_results:
        logger.info("   💰 Financial data available (%d records)", len(financial_results))

    # Check if we have any data to analyze
    if not graph_results and not vector_results and not web_results and not web_ai_answer and not financial_results:
        logger.warning("   No data to analyze!")
        return {
            "entities_found": [],
            "relationships_found": [],
            "insights": [],
            "synthesis": "I couldn't find relevant information to analyze for this query.",
        }
    
    llm = get_llm(temperature=0.3)  # Slightly creative for synthesis
    
    # Build the analysis prompt
    prompt = ANALYZER_PROMPT.format(
        query=query,
        query_type=query_type,
        graph_data=_format_results(graph_results),
        vector_data=_format_results(vector_results),
        web_data=_format_results(web_results),
        web_ai_summary=web_ai_answer if web_ai_answer else "No AI summary available.",
        financial_data=_format_financial_results(financial_results),
    )
    
    response = llm.invoke(prompt)
    analysis = _parse_analysis_response(response.content)
    
    # Extract and structure the results
    insights = analysis.get("insights", [])
    entities = analysis.get("entities_found", [])
    relationships = analysis.get("relationships_found", [])
    synthesis = analysis.get("synthesis", "")
    gaps = analysis.get("gaps_identified", [])
    
    logger.info("   Found %d entities, %d relationships, %d insights",
               len(entities), len(relationships), len(insights))
    
    if gaps:
        logger.info("   Gaps identified: %s", ", ".join(gaps[:3]))
    
    return {
        "entities_found": entities,
        "relationships_found": relationships,
        "insights": insights,
        "synthesis": synthesis,
    }