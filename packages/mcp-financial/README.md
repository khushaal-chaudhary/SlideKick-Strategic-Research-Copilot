# Financial Data MCP Server

A Model Context Protocol (MCP) server that provides financial data tools powered by [Alpha Vantage API](https://www.alphavantage.co/) for the Strategic Research Copilot.

## Features

- Real-time stock quotes and price data
- Company fundamentals and valuation metrics
- Income statement data (annual/quarterly)
- News sentiment analysis
- Multi-company comparison

## Tools Provided

| Tool | Description |
|------|-------------|
| `get_company_overview` | Get company info, fundamentals, and valuation metrics (P/E, EPS, profit margin, etc.) |
| `get_stock_quote` | Get current stock price, change, and trading volume |
| `get_income_statement` | Get income statement data (revenue, profit, EBITDA) |
| `get_news_sentiment` | Get recent news with sentiment analysis |
| `compare_companies` | Compare metrics across multiple companies (max 5) |

## Prerequisites

1. **Alpha Vantage API Key** (Free tier available)
   - Get your free key at: https://www.alphavantage.co/support/#api-key
   - Free tier: 25 requests/day, 5 requests/minute

2. **Node.js 20+**

## Setup

1. **Get an Alpha Vantage API key:**
   ```
   Visit: https://www.alphavantage.co/support/#api-key
   ```

2. **Set environment variable:**
   ```bash
   # Add to your .env file or shell profile
   export ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Build:**
   ```bash
   npm run build
   ```

5. **Run (stdio mode):**
   ```bash
   npm start
   ```

## Integration with Python Agent

The Python agent can connect to this MCP server using the `mcp` package:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def get_financial_data(symbol: str):
    server_params = StdioServerParameters(
        command="node",
        args=["path/to/dist/index.js"],
        env={"ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY")}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get company overview
            result = await session.call_tool(
                "get_company_overview",
                arguments={"symbol": "MSFT"}
            )

            return result.content[0].text
```

## Example Usage

### Get Company Overview
```json
{
  "tool": "get_company_overview",
  "arguments": {
    "symbol": "MSFT"
  }
}
```

Returns: Market cap, P/E ratio, EPS, profit margin, sector, industry, etc.

### Get Stock Quote
```json
{
  "tool": "get_stock_quote",
  "arguments": {
    "symbol": "AAPL"
  }
}
```

Returns: Current price, change, volume, open/high/low, etc.

### Get Income Statement
```json
{
  "tool": "get_income_statement",
  "arguments": {
    "symbol": "GOOGL",
    "period": "annual"
  }
}
```

Returns: Revenue, gross profit, operating income, net income, EBITDA.

### Get News Sentiment
```json
{
  "tool": "get_news_sentiment",
  "arguments": {
    "symbol": "TSLA",
    "limit": 5
  }
}
```

Returns: Recent news articles with sentiment analysis.

### Compare Companies
```json
{
  "tool": "compare_companies",
  "arguments": {
    "symbols": ["MSFT", "AAPL", "GOOGL"]
  }
}
```

Returns: Side-by-side comparison of key metrics.

## Rate Limits

Alpha Vantage free tier limits:
- **25 requests per day**
- **5 requests per minute**

The MCP server includes built-in delays for multi-symbol requests to avoid rate limiting.

## Testing

```bash
# Type check
npm run typecheck

# Lint
npm run lint

# Manual test with MCP Inspector
npx @modelcontextprotocol/inspector node dist/index.js
```

## Troubleshooting

### "ALPHA_VANTAGE_API_KEY not set"
Ensure the environment variable is set before starting the server.

### "Alpha Vantage API rate limit reached"
Wait a minute and try again. Consider upgrading to a premium plan for higher limits.

### "Company not found"
Verify the stock ticker symbol is correct (e.g., MSFT, AAPL, GOOGL).

## License

MIT
