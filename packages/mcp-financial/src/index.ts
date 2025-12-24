/**
 * Financial Data MCP Server
 *
 * This MCP server provides tools for retrieving financial data
 * from Alpha Vantage API for the Strategic Research Copilot.
 *
 * Tools:
 * - get_company_overview: Get basic company information and fundamentals
 * - get_stock_quote: Get current stock price and trading data
 * - get_income_statement: Get income statement data
 * - get_news_sentiment: Get recent news with sentiment analysis
 * - compare_companies: Compare metrics across companies
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

// =============================================================================
// Configuration
// =============================================================================

const ALPHA_VANTAGE_API_KEY = process.env.ALPHA_VANTAGE_API_KEY || "";
const ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query";

// =============================================================================
// Tool Definitions
// =============================================================================

const TOOLS: Tool[] = [
  {
    name: "get_company_overview",
    description:
      "Get an overview of a company including sector, industry, fundamentals, and valuation metrics",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "Stock ticker symbol (e.g., MSFT, GOOGL, AAPL)",
        },
      },
      required: ["symbol"],
    },
  },
  {
    name: "get_stock_quote",
    description: "Get current stock price, change, and trading volume",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "Stock ticker symbol",
        },
      },
      required: ["symbol"],
    },
  },
  {
    name: "get_income_statement",
    description:
      "Get income statement data including revenue, profit, and EBITDA",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "Stock ticker symbol",
        },
        period: {
          type: "string",
          enum: ["annual", "quarterly"],
          description: "Report period (default: annual)",
        },
      },
      required: ["symbol"],
    },
  },
  {
    name: "get_news_sentiment",
    description:
      "Get recent news articles with sentiment analysis for a company",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "Stock ticker symbol",
        },
        limit: {
          type: "number",
          description: "Maximum number of articles to return (default: 10)",
        },
      },
      required: ["symbol"],
    },
  },
  {
    name: "compare_companies",
    description:
      "Compare key financial metrics across multiple companies",
    inputSchema: {
      type: "object",
      properties: {
        symbols: {
          type: "array",
          items: { type: "string" },
          description: "List of stock ticker symbols to compare (max 5)",
        },
      },
      required: ["symbols"],
    },
  },
];

// =============================================================================
// Alpha Vantage API Helpers
// =============================================================================

async function fetchAlphaVantage(
  functionType: string,
  params: Record<string, string>
): Promise<unknown> {
  if (!ALPHA_VANTAGE_API_KEY) {
    throw new Error(
      "ALPHA_VANTAGE_API_KEY environment variable not set. Get a free key at https://www.alphavantage.co/support/#api-key"
    );
  }

  const url = new URL(ALPHA_VANTAGE_BASE_URL);
  url.searchParams.set("function", functionType);
  url.searchParams.set("apikey", ALPHA_VANTAGE_API_KEY);

  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const response = await axios.get(url.toString());

  // Check for API errors
  if (response.data["Error Message"]) {
    throw new Error(response.data["Error Message"]);
  }
  if (response.data["Note"]) {
    // Rate limit message
    throw new Error(
      "Alpha Vantage API rate limit reached. Please wait and try again."
    );
  }

  return response.data;
}

// =============================================================================
// Tool Handlers
// =============================================================================

async function handleGetCompanyOverview(symbol: string): Promise<string> {
  try {
    const data = (await fetchAlphaVantage("OVERVIEW", {
      symbol: symbol.toUpperCase(),
    })) as Record<string, string>;

    if (!data.Symbol) {
      return JSON.stringify({
        error: `Company not found: ${symbol}`,
        suggestion: "Please verify the stock ticker symbol",
      });
    }

    return JSON.stringify(
      {
        symbol: data.Symbol,
        name: data.Name,
        description: data.Description,
        sector: data.Sector,
        industry: data.Industry,
        marketCap: data.MarketCapitalization,
        peRatio: data.PERatio,
        pegRatio: data.PEGRatio,
        bookValue: data.BookValue,
        dividendPerShare: data.DividendPerShare,
        dividendYield: data.DividendYield,
        eps: data.EPS,
        revenuePerShareTTM: data.RevenuePerShareTTM,
        profitMargin: data.ProfitMargin,
        operatingMarginTTM: data.OperatingMarginTTM,
        returnOnAssetsTTM: data.ReturnOnAssetsTTM,
        returnOnEquityTTM: data.ReturnOnEquityTTM,
        revenueTTM: data.RevenueTTM,
        grossProfitTTM: data.GrossProfitTTM,
        quarterlyEarningsGrowthYOY: data.QuarterlyEarningsGrowthYOY,
        quarterlyRevenueGrowthYOY: data.QuarterlyRevenueGrowthYOY,
        analystTargetPrice: data.AnalystTargetPrice,
        week52High: data["52WeekHigh"],
        week52Low: data["52WeekLow"],
        beta: data.Beta,
      },
      null,
      2
    );
  } catch (error) {
    return JSON.stringify({
      error: `Failed to get company overview: ${error}`,
    });
  }
}

async function handleGetStockQuote(symbol: string): Promise<string> {
  try {
    const data = (await fetchAlphaVantage("GLOBAL_QUOTE", {
      symbol: symbol.toUpperCase(),
    })) as { "Global Quote": Record<string, string> };

    const quote = data["Global Quote"];
    if (!quote || !quote["01. symbol"]) {
      return JSON.stringify({
        error: `Quote not found for: ${symbol}`,
        suggestion: "Please verify the stock ticker symbol",
      });
    }

    return JSON.stringify(
      {
        symbol: quote["01. symbol"],
        price: quote["05. price"],
        change: quote["09. change"],
        changePercent: quote["10. change percent"],
        open: quote["02. open"],
        high: quote["03. high"],
        low: quote["04. low"],
        volume: quote["06. volume"],
        latestTradingDay: quote["07. latest trading day"],
        previousClose: quote["08. previous close"],
      },
      null,
      2
    );
  } catch (error) {
    return JSON.stringify({
      error: `Failed to get stock quote: ${error}`,
    });
  }
}

async function handleGetIncomeStatement(
  symbol: string,
  period: string = "annual"
): Promise<string> {
  try {
    const data = (await fetchAlphaVantage("INCOME_STATEMENT", {
      symbol: symbol.toUpperCase(),
    })) as {
      annualReports?: Array<Record<string, string>>;
      quarterlyReports?: Array<Record<string, string>>;
    };

    const reports =
      period === "quarterly" ? data.quarterlyReports : data.annualReports;

    if (!reports || reports.length === 0) {
      return JSON.stringify({
        error: `Income statement not found for: ${symbol}`,
      });
    }

    // Get the latest report
    const latest = reports[0];

    return JSON.stringify(
      {
        symbol: symbol.toUpperCase(),
        fiscalDateEnding: latest.fiscalDateEnding,
        reportedCurrency: latest.reportedCurrency,
        totalRevenue: latest.totalRevenue,
        grossProfit: latest.grossProfit,
        operatingIncome: latest.operatingIncome,
        netIncome: latest.netIncome,
        ebitda: latest.ebitda,
        costOfRevenue: latest.costOfRevenue,
        researchAndDevelopment: latest.researchAndDevelopment,
        operatingExpenses: latest.operatingExpenses,
        interestExpense: latest.interestExpense,
        period: period,
      },
      null,
      2
    );
  } catch (error) {
    return JSON.stringify({
      error: `Failed to get income statement: ${error}`,
    });
  }
}

async function handleGetNewsSentiment(
  symbol: string,
  limit: number = 10
): Promise<string> {
  try {
    const data = (await fetchAlphaVantage("NEWS_SENTIMENT", {
      tickers: symbol.toUpperCase(),
      limit: String(Math.min(limit, 50)),
    })) as {
      feed?: Array<{
        title: string;
        url: string;
        time_published: string;
        summary: string;
        source: string;
        overall_sentiment_label: string;
        overall_sentiment_score: number;
        ticker_sentiment?: Array<{
          ticker: string;
          relevance_score: string;
          ticker_sentiment_label: string;
        }>;
      }>;
    };

    if (!data.feed || data.feed.length === 0) {
      return JSON.stringify({
        symbol: symbol.toUpperCase(),
        articles: [],
        message: "No recent news found",
      });
    }

    const articles = data.feed.slice(0, limit).map((article) => {
      const tickerSentiment = article.ticker_sentiment?.find(
        (t) => t.ticker === symbol.toUpperCase()
      );
      return {
        title: article.title,
        source: article.source,
        publishedAt: article.time_published,
        summary: article.summary?.substring(0, 200),
        url: article.url,
        overallSentiment: article.overall_sentiment_label,
        sentimentScore: article.overall_sentiment_score,
        tickerRelevance: tickerSentiment?.relevance_score,
        tickerSentiment: tickerSentiment?.ticker_sentiment_label,
      };
    });

    return JSON.stringify(
      {
        symbol: symbol.toUpperCase(),
        articleCount: articles.length,
        articles,
      },
      null,
      2
    );
  } catch (error) {
    return JSON.stringify({
      error: `Failed to get news sentiment: ${error}`,
    });
  }
}

async function handleCompareCompanies(symbols: string[]): Promise<string> {
  try {
    // Limit to 5 companies to avoid rate limits
    const limitedSymbols = symbols.slice(0, 5);
    const comparisons: Array<Record<string, unknown>> = [];

    for (const symbol of limitedSymbols) {
      try {
        const data = (await fetchAlphaVantage("OVERVIEW", {
          symbol: symbol.toUpperCase(),
        })) as Record<string, string>;

        if (data.Symbol) {
          comparisons.push({
            symbol: data.Symbol,
            name: data.Name,
            sector: data.Sector,
            marketCap: data.MarketCapitalization,
            peRatio: data.PERatio,
            eps: data.EPS,
            profitMargin: data.ProfitMargin,
            revenueTTM: data.RevenueTTM,
            returnOnEquityTTM: data.ReturnOnEquityTTM,
            dividendYield: data.DividendYield,
            week52High: data["52WeekHigh"],
            week52Low: data["52WeekLow"],
          });
        }

        // Add delay to avoid rate limits (5 calls/minute for free tier)
        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch {
        comparisons.push({
          symbol: symbol.toUpperCase(),
          error: "Failed to fetch data",
        });
      }
    }

    return JSON.stringify(
      {
        comparison: comparisons,
        symbolsRequested: symbols.length,
        symbolsReturned: comparisons.length,
        note:
          symbols.length > 5
            ? "Limited to 5 companies to avoid API rate limits"
            : undefined,
      },
      null,
      2
    );
  } catch (error) {
    return JSON.stringify({
      error: `Failed to compare companies: ${error}`,
    });
  }
}

// =============================================================================
// Server Setup
// =============================================================================

const server = new Server(
  {
    name: "financial-data-mcp",
    version: "0.2.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result: string;

    switch (name) {
      case "get_company_overview":
        result = await handleGetCompanyOverview(args?.symbol as string);
        break;

      case "get_stock_quote":
        result = await handleGetStockQuote(args?.symbol as string);
        break;

      case "get_income_statement":
        result = await handleGetIncomeStatement(
          args?.symbol as string,
          (args?.period as string) || "annual"
        );
        break;

      case "get_news_sentiment":
        result = await handleGetNewsSentiment(
          args?.symbol as string,
          (args?.limit as number) || 10
        );
        break;

      case "compare_companies":
        result = await handleCompareCompanies(args?.symbols as string[]);
        break;

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }

    return {
      content: [{ type: "text", text: result }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error}` }],
      isError: true,
    };
  }
});

// =============================================================================
// Main Entry Point
// =============================================================================

async function main() {
  if (!ALPHA_VANTAGE_API_KEY) {
    console.error(
      "Warning: ALPHA_VANTAGE_API_KEY not set. Get a free key at https://www.alphavantage.co/support/#api-key"
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Financial Data MCP server running on stdio (Alpha Vantage)");
}

main().catch(console.error);
