# Strategic Research Copilot API

FastAPI backend for the Strategic Research Copilot web interface, designed for deployment on Hugging Face Spaces.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/query` | POST | Submit a research query |
| `/api/stream/{session_id}` | GET | SSE stream for real-time logs |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 7860
```

## Deployment to Hugging Face Spaces

1. Create a new Space with Docker SDK
2. Push this directory to the Space
3. Configure environment variables in Space settings

### Required Environment Variables

```
GOOGLE_API_KEY=your_key
NEO4J_URI=your_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
TAVILY_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

## Architecture

```
┌─────────────────┐     SSE      ┌─────────────────┐
│   Next.js Web   │ ◄──────────► │   FastAPI API   │
│   (Vercel)      │              │ (HF Spaces)     │
└─────────────────┘              └────────┬────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  Research Agent │
                                 │  (LangGraph)    │
                                 └─────────────────┘
```
