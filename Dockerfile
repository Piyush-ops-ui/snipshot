# ==============================================================================
# SnipShot Dockerfile: 100% Free Deployment on Hugging Face Spaces (Port 7860)
# Multi-stage build combining React frontend and FastAPI backend with native FFmpeg
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend (Vite + React + Tailwind)
# ------------------------------------------------------------------------------
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend manifests
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci || npm install

# Copy frontend source code and configuration
COPY frontend/ ./

# Compile production single-page application into /app/frontend/dist
RUN npm run build


# ------------------------------------------------------------------------------
# Stage 2: Python Backend Runtime & Single-Origin Production Serving
# ------------------------------------------------------------------------------
FROM python:3.11-slim

# Prevent python buffering and configure Hugging Face / Torch cache paths
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HF_HOME=/app/data/cache/huggingface \
    TORCH_HOME=/app/data/cache/torch

WORKDIR /app

# Install system dependencies:
# - ffmpeg: audio extraction, 9:16 layout compositing, ASS subtitle burning
# - libgl1 & libglib2.0-0: opencv-python-headless & RapidOCR
# - espeak-ng: neural phoneme alignment & speech synthesis
# - curl & git: model downloads & container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    espeak-ng \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Pre-download faster-whisper small & base models so container boots instantly
RUN mkdir -p /app/data/cache/huggingface && \
    python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8'); WhisperModel('small', device='cpu', compute_type='int8')"

# Copy compiled frontend distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy backend application code
COPY backend/ /app/backend/

# Copy data directory (including bundled demo_clips and cache)
COPY data/ /app/data/

# Create and grant full permissions to writable directories
RUN mkdir -p \
    /app/data/cache \
    /app/data/cache/provenance \
    /app/data/cache/huggingface \
    /app/data/uploads \
    /app/data/exports \
    /app/data/db \
    /app/data/demo_clips \
    /app/backend/outputs && \
    chmod -R 777 /app/data /app/backend/outputs

# Create non-root user matching Hugging Face Spaces default UID 1000
RUN useradd -m -u 1000 user && \
    chown -R user:user /app
USER user

# Expose Hugging Face Spaces default port
EXPOSE 7860

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start FastAPI server on port 7860
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
