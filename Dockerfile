# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder
# CACHE_BUST: 3 — bump this number to force Railway to rebuild from scratch
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .

# Install order matters:
#   1. numpy<2  — torch & shap were compiled against NumPy 1.x API.
#                 NumPy 2.x breaks them at runtime.
#   2. torch    — CPU-only wheel (~800 MB saved vs CUDA build).
#                 2.5.1 satisfies transformers>=4.40 requirement (needs >=2.5).
#   3. rest     — everything else in requirements.txt after torch is in place.
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir "numpy>=1.24,<2.0" && \
    pip install --no-cache-dir \
        "torch==2.5.1" \
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

COPY api/           ./api/
COPY src/           ./src/
COPY config.py      ./config.py
COPY models/        ./models/
COPY data/raw/live/ ./data/raw/live/

ENV PORT=8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 120"]
