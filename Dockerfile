# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder — installs all Python deps into /install
# Using slim-bullseye keeps the final image smaller while still having the
# C/Fortran toolchain that numpy/shap need to compile.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bullseye AS builder

# Build-time system deps (gcc etc. needed by numpy, shap, some tokenizers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Copy requirements first so Docker layer-caches the install
# and only re-runs pip when requirements.txt actually changes.
COPY requirements.txt .

# --no-cache-dir saves ~200 MB in the image
# Install CPU-only PyTorch from the official index so we don't pull the
# 2 GB CUDA wheel (Railway runs on CPU).
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir \
        torch==2.2.2 \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: runtime — only the files the server actually needs
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bullseye AS runtime

# Runtime-only system libs (no gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy the application code
# Deliberately copy only what the API needs at runtime:
#   api/        — FastAPI app
#   src/        — ML pipeline (features, model, sentiment, collect, utils)
#   config.py   — all settings
#   models/     — frozen XGBoost artifact + feature_order.json
#   data/raw/live/ — demo-day fallback snapshots
COPY api/        ./api/
COPY src/        ./src/
COPY config.py   ./config.py
COPY models/     ./models/
COPY data/raw/live/ ./data/raw/live/

# Railway injects PORT at runtime; default to 8000 for local testing.
ENV PORT=8000

# Tell uvicorn to bind to whatever port Railway provides.
# --workers 1 because Railway's free tier is single-CPU and SHAP/torch
# aren't designed for forked workers sharing memory.
CMD uvicorn api.main:app \
        --host 0.0.0.0 \
        --port $PORT \
        --workers 1 \
        --timeout-keep-alive 120
