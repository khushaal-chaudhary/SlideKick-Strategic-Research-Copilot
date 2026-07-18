# =============================================================================
# SlideKick - Strategic Research Copilot
# Dockerfile for Hugging Face Spaces with Ollama
# =============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for Ollama
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create non-root user (required by HF Spaces)
RUN useradd -m -u 1000 user

# Create ollama directory with proper permissions
RUN mkdir -p /home/user/.ollama && chown -R user:user /home/user/.ollama

# Switch to user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODELS=/home/user/.ollama/models

# Set working directory for user
WORKDIR /home/user/app

# Copy requirements first for better caching
COPY --chown=user:user api/requirements.txt ./requirements.txt

# Install Python dependencies (torch first from the CPU wheel index so
# sentence-transformers doesn't drag in the multi-GB CUDA build)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Bake the rerank cross-encoder into the image to avoid cold-start downloads
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy the agent package
COPY --chown=user:user packages/agent/src/copilot ./copilot

# Copy the API
COPY --chown=user:user api/ ./

# Copy eval results (served at /api/evals/latest)
COPY --chown=user:user evals/results ./evals/results

# Copy startup script
COPY --chown=user:user start.sh ./start.sh
RUN chmod +x ./start.sh

# Set Python path to include copilot package
ENV PYTHONPATH=/home/user/app:$PYTHONPATH

# Expose ports (7860 for API, 11434 for Ollama)
EXPOSE 7860 11434

# Run the startup script
CMD ["./start.sh"]
