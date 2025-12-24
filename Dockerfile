# =============================================================================
# SlideKick - Strategic Research Copilot
# Dockerfile for Hugging Face Spaces
# =============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (required by HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory for user
WORKDIR /home/user/app

# Copy requirements first for better caching
COPY --chown=user:user api/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the agent package
COPY --chown=user:user packages/agent/src/copilot ./copilot

# Copy the API
COPY --chown=user:user api/ ./

# Set Python path to include copilot package
ENV PYTHONPATH=/home/user/app:$PYTHONPATH

# Expose port 7860 (HF Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
