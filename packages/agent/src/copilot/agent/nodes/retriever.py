"""
Retriever Node - Tool Executor for Data Retrieval.

This node executes retrieval based on:
1. Initial query → Knowledge graph search
2. Critic's refinement_type → Execute requested tool (web, vector, etc.)

The Critic decides WHAT tool to use. The Retriever just EXECUTES.
This separation of concerns makes the architecture cleaner and more agentic.

Web Search powered by Tavily - provides AI-summarized results with full content.
"""

import logging
from typing import Any

from copilot.agent.state import ResearchState, RefinementType, RetrievalStrategy
from copilot.config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Data Source Functions (Tools)
# =============================================================================

def _query_graph(query: str, entities: list[str]) -> dict[str, Any]:
    """
    Query the Neo4j knowledge graph.
    
    Args:
        query: Search query
        entities: Specific entities to focus on
        
    Returns:
        Dict with source, results, count, and confidence
    """
    from copilot.graph.connection import graph_connection
    
    results = []
    
    try:
        # Strategy 1: Search by entities if we have them
        if entities:
            for entity in entities[:5]:  # Limit to avoid overquerying
                cypher = """
                    MATCH (n)-[r]-(m)
                    WHERE toLower(n.id) CONTAINS toLower($entity)
                    RETURN n.id AS source, type(r) AS relationship, 
                           m.id AS target, labels(n) AS source_type, labels(m) AS target_type
                    LIMIT 20
                """
                entity_results = graph_connection.query(cypher, params={"entity": entity})
                results.extend(entity_results)
        
        # Strategy 2: General search with key terms from query
        cypher = """
            MATCH (n)
            WHERE toLower(n.id) CONTAINS toLower($search)
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n.id AS entity, labels(n) AS types, 
                   collect(DISTINCT {rel: type(r), target: m.id})[..5] AS relationships
            LIMIT 30
        """
        search_terms = query.lower().split()[:3]
        for term in search_terms:
            if len(term) > 3:
                query_results = graph_connection.query(cypher, params={"search": term})
                results.extend(query_results)
        
        # Deduplicate
        seen = set()
        unique_results = []
        for r in results:
            key = str(r.get("entity", r.get("source", "")))
            if key and key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        confidence = min(1.0, len(unique_results) / 10)
        
        return {
            "source": "knowledge_graph",
            "query": query,
            "results": unique_results[:30],
            "result_count": len(unique_results),
            "confidence": confidence,
        }
        
    except Exception as e:
        logger.error("Graph query failed: %s", e)
        return {
            "source": "knowledge_graph",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


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
        
        # Use advanced search for better results
        response = client.search(
            query=query,
            search_depth="advanced",  # More thorough search
            max_results=max_results,
            include_answer=True,       # Get AI-generated summary!
            include_raw_content=False, # We don't need raw HTML
        )
        
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


def _query_vector(query: str, top_k: int = 5) -> dict[str, Any]:
    """
    Query vector embeddings for semantic similarity search.
    
    Uses Ollama embeddings (nomic-embed-text) + Neo4j vector index
    to find semantically similar document chunks.
    
    Args:
        query: Search query
        top_k: Number of results to return
        
    Returns:
        Dict with source, results (text passages), count, confidence
    """
    logger.info("   🔮 Executing vector search: '%s'", query[:60])
    
    try:
        from langchain_ollama import OllamaEmbeddings
        from copilot.graph.connection import graph_connection
        
        # Initialize embeddings (nomic-embed-text = 768 dimensions)
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # Generate query embedding
        query_embedding = embeddings.embed_query(query)
        
        # Query Neo4j vector index
        cypher = """
            CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding)
            YIELD node, score
            RETURN 
                node.id AS chunk_id,
                node.text AS text,
                node.source AS source,
                score
            ORDER BY score DESC
        """
        
        results = graph_connection.query(cypher, params={
            "embedding": query_embedding,
            "top_k": top_k,
        })
        
        # Format results
        formatted = []
        for r in results:
            formatted.append({
                "chunk_id": r.get("chunk_id"),
                "text": r.get("text", ""),
                "source": r.get("source", "unknown"),
                "score": r.get("score", 0.0),
                "source_type": "vector",
            })
        
        # Confidence based on top score
        top_score = formatted[0]["score"] if formatted else 0.0
        confidence = min(1.0, top_score)  # Score is already 0-1 for cosine
        
        logger.info("   🔮 Vector search found %d results (top score: %.3f)", 
                   len(formatted), top_score)
        
        return {
            "source": "vector_search",
            "query": query,
            "results": formatted,
            "result_count": len(formatted),
            "confidence": confidence,
        }
        
    except ImportError as e:
        logger.warning("   ⚠️ langchain-ollama not installed: %s", e)
        return {
            "source": "vector_search",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": "langchain-ollama not installed. Run: pip install langchain-ollama",
        }
    except Exception as e:
        logger.error("   ❌ Vector search failed: %s", e)
        return {
            "source": "vector_search",
            "query": query,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


def _query_financial_data(symbols: list[str], query: str = "") -> dict[str, Any]:
    """
    Query Alpha Vantage API for financial data.

    Retrieves company fundamentals, stock quotes, and financial metrics
    for the given stock symbols.

    Args:
        symbols: List of stock ticker symbols (e.g., ["MSFT", "AAPL"])
        query: Original query for context (used for news sentiment)

    Returns:
        Dict with source, results (company data, quotes, metrics), count, confidence
    """
    import requests

    logger.info("   💰 Executing financial data query for: %s", symbols)

    api_key = settings.alpha_vantage_api_key_str

    if not api_key or api_key == "your_alpha_vantage_api_key_here":
        logger.warning("   ⚠️ ALPHA_VANTAGE_API_KEY not set, skipping financial data")
        return {
            "source": "financial_data",
            "query": query,
            "symbols": symbols,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": "ALPHA_VANTAGE_API_KEY not configured. Get free key at alphavantage.co",
        }

    base_url = "https://www.alphavantage.co/query"
    results = []

    try:
        for symbol in symbols[:5]:  # Limit to 5 symbols to avoid rate limits
            symbol = symbol.upper().strip()
            company_data = {"symbol": symbol}

            # 1. Get Company Overview (fundamentals)
            try:
                overview_resp = requests.get(
                    base_url,
                    params={"function": "OVERVIEW", "symbol": symbol, "apikey": api_key},
                    timeout=10,
                )
                overview = overview_resp.json()

                if "Symbol" in overview:
                    company_data["overview"] = {
                        "name": overview.get("Name", ""),
                        "description": overview.get("Description", "")[:500],
                        "sector": overview.get("Sector", ""),
                        "industry": overview.get("Industry", ""),
                        "market_cap": overview.get("MarketCapitalization", ""),
                        "pe_ratio": overview.get("PERatio", ""),
                        "eps": overview.get("EPS", ""),
                        "dividend_yield": overview.get("DividendYield", ""),
                        "52_week_high": overview.get("52WeekHigh", ""),
                        "52_week_low": overview.get("52WeekLow", ""),
                        "profit_margin": overview.get("ProfitMargin", ""),
                        "revenue_ttm": overview.get("RevenueTTM", ""),
                        "gross_profit_ttm": overview.get("GrossProfitTTM", ""),
                    }
                    logger.info("   📊 Got overview for %s: %s", symbol, overview.get("Name", ""))
                elif "Note" in overview:
                    # API rate limit hit
                    logger.warning("   ⚠️ Alpha Vantage rate limit: %s", overview.get("Note", ""))
                    company_data["error"] = "API rate limit reached"
            except Exception as e:
                logger.warning("   ⚠️ Failed to get overview for %s: %s", symbol, e)

            # 2. Get Current Stock Quote
            try:
                quote_resp = requests.get(
                    base_url,
                    params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
                    timeout=10,
                )
                quote = quote_resp.json()

                if "Global Quote" in quote and quote["Global Quote"]:
                    gq = quote["Global Quote"]
                    company_data["quote"] = {
                        "price": gq.get("05. price", ""),
                        "change": gq.get("09. change", ""),
                        "change_percent": gq.get("10. change percent", ""),
                        "volume": gq.get("06. volume", ""),
                        "latest_trading_day": gq.get("07. latest trading day", ""),
                        "previous_close": gq.get("08. previous close", ""),
                    }
                    logger.info("   📈 Got quote for %s: $%s", symbol, gq.get("05. price", "N/A"))
            except Exception as e:
                logger.warning("   ⚠️ Failed to get quote for %s: %s", symbol, e)

            # 3. Get Income Statement (annual)
            try:
                income_resp = requests.get(
                    base_url,
                    params={"function": "INCOME_STATEMENT", "symbol": symbol, "apikey": api_key},
                    timeout=10,
                )
                income = income_resp.json()

                if "annualReports" in income and income["annualReports"]:
                    latest = income["annualReports"][0]
                    company_data["income_statement"] = {
                        "fiscal_year": latest.get("fiscalDateEnding", ""),
                        "total_revenue": latest.get("totalRevenue", ""),
                        "gross_profit": latest.get("grossProfit", ""),
                        "operating_income": latest.get("operatingIncome", ""),
                        "net_income": latest.get("netIncome", ""),
                        "ebitda": latest.get("ebitda", ""),
                    }
                    logger.info("   📑 Got income statement for %s", symbol)
            except Exception as e:
                logger.warning("   ⚠️ Failed to get income statement for %s: %s", symbol, e)

            results.append(company_data)

        # 4. Get News Sentiment (if we have a query)
        if query and symbols:
            try:
                # Use first symbol for news
                news_resp = requests.get(
                    base_url,
                    params={
                        "function": "NEWS_SENTIMENT",
                        "tickers": ",".join(symbols[:3]),
                        "limit": 5,
                        "apikey": api_key,
                    },
                    timeout=10,
                )
                news = news_resp.json()

                if "feed" in news:
                    news_items = []
                    for item in news["feed"][:5]:
                        news_items.append({
                            "title": item.get("title", ""),
                            "source": item.get("source", ""),
                            "summary": item.get("summary", "")[:300],
                            "sentiment": item.get("overall_sentiment_label", ""),
                            "sentiment_score": item.get("overall_sentiment_score", ""),
                            "url": item.get("url", ""),
                        })
                    if news_items:
                        results.append({"news_sentiment": news_items})
                        logger.info("   📰 Got %d news articles", len(news_items))
            except Exception as e:
                logger.warning("   ⚠️ Failed to get news sentiment: %s", e)

        # Calculate confidence based on data completeness
        data_points = sum(
            1 for r in results
            if isinstance(r, dict) and ("overview" in r or "quote" in r)
        )
        confidence = min(1.0, data_points / max(len(symbols), 1))

        logger.info("   💰 Financial data retrieved: %d results", len(results))

        return {
            "source": "financial_data",
            "query": query,
            "symbols": symbols,
            "results": results,
            "result_count": len(results),
            "confidence": confidence,
        }

    except Exception as e:
        logger.error("   ❌ Financial data query failed: %s", e)
        return {
            "source": "financial_data",
            "query": query,
            "symbols": symbols,
            "results": [],
            "result_count": 0,
            "confidence": 0.0,
            "error": str(e),
        }


# =============================================================================
# Main Retriever Node
# =============================================================================

def retriever_node(state: ResearchState) -> dict[str, Any]:
    """
    Execute retrieval based on current state.

    Logic:
    - First iteration (or no refinement): Query knowledge graph (or financial data if FINANCIAL_FIRST)
    - Critic requested web_search: Execute Tavily web search
    - Critic requested vector_search: Execute vector search
    - Critic requested more_graph: Deeper graph exploration
    - Critic requested financial_data: Execute Alpha Vantage financial API

    The Critic decides WHAT. The Retriever EXECUTES.
    """
    query = state["original_query"]
    entities = state.get("entities_of_interest", [])
    iteration = state.get("iteration", 1)
    retrieval_strategy = state.get("retrieval_strategy", RetrievalStrategy.HYBRID.value)

    # What did the critic request?
    refinement_type = state.get("refinement_type", RefinementType.NONE.value)
    refinement_focus = state.get("refinement_focus", "")

    logger.info("🔍 Retriever: Iteration %d", iteration)
    logger.info("   Refinement type: %s", refinement_type)
    logger.info("   Strategy: %s", retrieval_strategy)

    # Get existing results (we accumulate, not replace)
    all_retrievals = list(state.get("all_retrievals", []))
    graph_results = list(state.get("graph_results", []))
    vector_results = list(state.get("vector_results", []))
    web_results = list(state.get("web_results", []))
    financial_results = list(state.get("financial_results", []))

    # Track AI answers from Tavily
    web_ai_answer = state.get("web_ai_answer", "")
    
    # ==========================================================================
    # Execute based on refinement_type
    # ==========================================================================
    
    if refinement_type == RefinementType.WEB_SEARCH.value:
        # Critic requested web search - use their optimized query
        search_query = refinement_focus if refinement_focus else query
        logger.info("   📡 Critic requested WEB_SEARCH")
        
        result = _query_web_tavily(search_query)
        web_results.extend(result["results"])
        all_retrievals.append(result)
        
        # Capture the AI-generated answer
        if result.get("ai_answer"):
            web_ai_answer = result["ai_answer"]
        
    elif refinement_type == RefinementType.VECTOR_SEARCH.value:
        # Critic requested vector search
        search_query = refinement_focus if refinement_focus else query
        logger.info("   📡 Critic requested VECTOR_SEARCH")
        
        result = _query_vector(search_query)
        vector_results.extend(result["results"])
        all_retrievals.append(result)
        
    elif refinement_type == RefinementType.MORE_GRAPH.value:
        # Critic wants deeper graph exploration
        search_query = refinement_focus if refinement_focus else query
        logger.info("   📡 Critic requested MORE_GRAPH")

        # Use refinement focus as additional entity
        additional_entities = [refinement_focus] if refinement_focus else []
        result = _query_graph(search_query, entities + additional_entities)
        graph_results.extend(result["results"])
        all_retrievals.append(result)

    elif refinement_type == RefinementType.FINANCIAL_DATA.value:
        # Critic requested financial data - use stock_symbols from planner
        logger.info("   📡 Critic requested FINANCIAL_DATA")

        # Get stock symbols from state (set by planner) or refinement_focus
        symbols = list(state.get("stock_symbols", []))
        if refinement_focus:
            # Refinement focus might contain comma-separated symbols
            symbols.extend([s.strip().upper() for s in refinement_focus.split(",")])
        # Deduplicate
        symbols = list(dict.fromkeys(symbols))

        if symbols:
            result = _query_financial_data(symbols, query)
            financial_results.extend(result["results"])
            all_retrievals.append(result)
        else:
            logger.warning("   ⚠️ No stock symbols found for financial data query")

    else:
        # First iteration OR no specific request
        # Check if FINANCIAL_FIRST strategy - query financial data first
        if retrieval_strategy == RetrievalStrategy.FINANCIAL_FIRST.value:
            logger.info("   💰 Strategy FINANCIAL_FIRST: Querying financial data")

            # Use stock_symbols from planner
            symbols = list(state.get("stock_symbols", []))
            if symbols:
                result = _query_financial_data(symbols, query)
                financial_results.extend(result["results"])
                all_retrievals.append(result)
            else:
                logger.warning("   ⚠️ No stock symbols, falling back to graph")
                result = _query_graph(query, entities)
                graph_results.extend(result["results"])
                all_retrievals.append(result)
        else:
            # Default: query knowledge graph
            logger.info("   📚 Default: Querying knowledge graph")

            result = _query_graph(query, entities)
            graph_results.extend(result["results"])
            all_retrievals.append(result)
    
    # Summary
    total = len(graph_results) + len(vector_results) + len(web_results) + len(financial_results)
    logger.info(
        "   📊 Total results: %d (graph=%d, vector=%d, web=%d, financial=%d)",
        total, len(graph_results), len(vector_results), len(web_results), len(financial_results)
    )

    # Return updated state - clear refinement_type after use
    return {
        "graph_results": graph_results,
        "vector_results": vector_results,
        "web_results": web_results,
        "web_ai_answer": web_ai_answer,  # Tavily's AI summary
        "financial_results": financial_results,  # Alpha Vantage financial data
        "all_retrievals": all_retrievals,
        "refinement_type": RefinementType.NONE.value,  # Clear after execution
        "refinement_focus": "",  # Clear after execution
    }