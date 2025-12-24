#!/bin/bash
# =============================================================================
# SlideKick Startup Script
# Starts Ollama, downloads model, then runs the API
# =============================================================================

set -e

echo "================================================"
echo "  SlideKick - Starting up..."
echo "================================================"

# Start Ollama server in background
echo "[1/4] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[2/4] Waiting for Ollama to be ready..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: Ollama failed to start after $max_attempts attempts"
        exit 1
    fi
    echo "  Waiting for Ollama... (attempt $attempt/$max_attempts)"
    sleep 2
done
echo "  Ollama is ready!"

# Pull the model (this is the slow part on cold start)
MODEL_NAME="${LLM_MODEL:-qwen2.5:7b}"
echo "[3/4] Pulling model: $MODEL_NAME"
echo "  This may take 5-10 minutes on first run..."
ollama pull "$MODEL_NAME"
echo "  Model downloaded successfully!"

# Start the FastAPI server
echo "[4/4] Starting SlideKick API..."
echo "================================================"
echo "  SlideKick is ready to kick!"
echo "  API: http://0.0.0.0:7860"
echo "  Ollama: http://0.0.0.0:11434"
echo "================================================"

exec uvicorn main:app --host 0.0.0.0 --port 7860
