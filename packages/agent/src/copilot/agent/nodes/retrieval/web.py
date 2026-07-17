"""Web-search retrieval node (Tavily)."""

import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from copilot.agent.state import ResearchState
from copilot.config.settings import settings

logger = logging.getLogger(__name__)


def _query_web_tavily(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Query the web using Tavily API.

    Tavily provides AI-powered search with:
    - AI-generated answer summarizing results
    - Full content extraction from pages (not just snippets!)
    - Relevance scoring

    Args:
        query: Search query (critic may have optimized this)
        max_results: Maximum results to return

    Returns:
        Dict with source, ai_answer, results (with full content), count, confidence
    """
    query = query[:400]  # Tavily rejects overly long queries
    logger.info("   🌐 Executing Tavily web search: '%s'", query[:60])

    api_key = settings.tavily_api_key_str

    if not api_key:
        logger.warning("   ⚠️ TAVILY_API_KEY not set, skipping web search")
        return {
            "source": "web_search",
            "query": query,
            "ai_answer": "",
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": "TAVILY_API_KEY not configured",
        }

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)

        # Retryable search call — transient network/server errors are common
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )
        def _tavily_search():
            return client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
            )

        response = _tavily_search()

        # Extract AI-generated answer
        ai_answer = response.get("answer", "")

        # Format results with FULL content (not snippets!)
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),  # FULL extracted content!
                "score": r.get("score", 0.0),     # Relevance score
                "source_type": "tavily",
            })

        # Sort by relevance score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        confidence = min(1.0, len(results) / 3)  # 3+ good results = high confidence

        logger.info("   🌐 Tavily found %d results", len(results))
        if ai_answer:
            logger.info("   🤖 AI Answer: %s...", ai_answer[:100])

        return {
            "source": "web_search",
            "query": query,
            "ai_answer": ai_answer,  # This is the gold - AI summary!
            "results": results,
            "result_count": len(results),
            "confidence": confidence,
        }

    except ImportError:
        logger.warning("   ⚠️ tavily-python not installed. Run: pip install tavily-python")
        return {
            "source": "web_search",
            "query": query,
            "ai_answer": "",
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": "tavily-python not installed",
        }
    except Exception as e:
        logger.error("   ❌ Tavily search failed: %s", e)
        return {
            "source": "web_search",
            "query": query,
            "ai_answer": "",
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


def web_retrieval_node(state: ResearchState) -> dict[str, Any]:
    """Run Tavily search; return only new results (reducer appends)."""
    query = state.get("refinement_focus") or state["original_query"]

    logger.info("   🌐 Web retrieval: '%s'", query[:60])
    result = _query_web_tavily(query)

    update: dict[str, Any] = {
        "web_results": result["results"],
        "all_retrievals": [result],
    }
    if result.get("ai_answer"):
        update["web_ai_answer"] = result["ai_answer"]
    return update
