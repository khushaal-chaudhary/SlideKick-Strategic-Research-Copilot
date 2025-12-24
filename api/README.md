# SlideKick API ⚡

The speed demon backend for SlideKick, designed for deployment on Hugging Face Spaces.

## Features

- **RESTful API** for query submission and session management
- **Server-Sent Events (SSE)** for real-time streaming updates
- **Session Management** for tracking research queries
- **Health Checks** for container orchestration

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| POST | `/api/query` | Submit a research query |
| GET | `/api/stream/{session_id}` | Stream real-time events (SSE) |
| GET | `/api/session/{session_id}` | Get session status |

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the server:
```bash
uvicorn main:app --reload --port 7860
```

5. Visit http://localhost:7860/docs for the Swagger UI

## SSE Event Types

The streaming endpoint emits the following event types:

| Event | Description |
|-------|-------------|
| `start` | Query processing started |
| `node_start` | Agent node started processing |
| `node_complete` | Agent node completed |
| `progress` | Iteration progress update |
| `retrieval` | Data retrieved from a source |
| `insight` | Analysis insight generated |
| `decision` | Critic decision made |
| `output` | Output being generated |
| `final_response` | Final response ready |
| `complete` | Processing complete |
| `error` | Error occurred |

## Deployment to Hugging Face Spaces

1. Create a new Space on Hugging Face (Docker SDK)
2. Push the `api/` directory contents
3. Set environment secrets in Space settings
4. The Dockerfile handles the rest

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

## Project Structure

```
api/
├── main.py          # FastAPI app and endpoints
├── config.py        # Settings and configuration
├── schemas.py       # Pydantic models
├── Dockerfile       # HF Spaces container
├── requirements.txt # Python dependencies
└── .env.example     # Environment template
```

## Author

Khushaal Chaudhary - [khushaalchaudhary.com](https://khushaalchaudhary.com)
