"""Financial-data retrieval node (Alpha Vantage)."""

import logging
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from copilot.agent.state import ResearchState
from copilot.config.settings import settings

logger = logging.getLogger(__name__)


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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def _av_get(params):
        return requests.get(base_url, params=params, timeout=10)

    try:
        for symbol in symbols[:5]:  # Limit to 5 symbols to avoid rate limits
            symbol = symbol.upper().strip()
            company_data = {"symbol": symbol}

            # 1. Get Company Overview (fundamentals)
            try:
                overview_resp = _av_get(
                    {"function": "OVERVIEW", "symbol": symbol, "apikey": api_key}
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
                quote_resp = _av_get(
                    {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}
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
                income_resp = _av_get(
                    {"function": "INCOME_STATEMENT", "symbol": symbol, "apikey": api_key}
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
                news_resp = _av_get({
                    "function": "NEWS_SENTIMENT",
                    "tickers": ",".join(symbols[:3]),
                    "limit": 5,
                    "apikey": api_key,
                })
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


def financial_retrieval_node(state: ResearchState) -> dict[str, Any]:
    """Fetch financial data; return only new results (reducer appends)."""
    symbols = list(state.get("stock_symbols", []))
    focus = state.get("refinement_focus", "")
    if focus:
        # Refinement focus might contain comma-separated symbols
        symbols.extend([s.strip().upper() for s in focus.split(",") if s.strip()])
    symbols = list(dict.fromkeys(symbols))

    if not symbols:
        logger.warning("   ⚠️ No stock symbols found for financial data query")
        return {}

    logger.info("   💰 Financial retrieval: %s", symbols)
    result = _query_financial_data(symbols, state["original_query"])

    return {
        "financial_results": result["results"],
        "all_retrievals": [result],
    }
