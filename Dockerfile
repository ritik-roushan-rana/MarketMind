# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder
# bookworm = Debian 12 (current stable, fully supported apt repos)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .

# CPU-only torch — no CUDA wheel (saves ~1.5 GB)
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir \
        torch==2.2.2 \
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

COPY api/          ./api/
COPY src/          ./src/
COPY config.py     ./config.py
COPY models/       ./models/
COPY data/raw/live/ ./data/raw/live/

ENV PORT=8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 120"]
