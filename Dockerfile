# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder — install all Python dependencies
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .

RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir "numpy>=1.24,<2.0" && \
    pip install --no-cache-dir \
        "torch==2.6.0" \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy source code and config first
COPY api/       ./api/
COPY src/       ./src/
COPY config.py  ./config.py

COPY models/ ./models/

COPY data/raw/live/ ./data/raw/live/

# No ENV PORT here on purpose. Railway injects its own $PORT and overrides
# anything set at build time, so hardcoding one only creates a misleading
# value to point a domain at. ${PORT:-8000} keeps `docker run` working
# locally while always deferring to the platform in production.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 120"]
