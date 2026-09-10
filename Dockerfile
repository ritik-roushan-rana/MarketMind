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

# Copy source code and config first
COPY api/       ./api/
COPY src/       ./src/
COPY config.py  ./config.py

# Copy models LAST and with an inline fix script so the base_score is
# always corrected at build time — regardless of what's in the cached layer.
# This also means any change to models/ triggers a fresh COPY.
COPY models/ ./models/

# Fix model.json base_score in-place at build time so SHAP never sees the
# array format '[5E-1,5E-1,5E-1]' that it cannot parse.
RUN python - <<'PYEOF'
import json, re, pathlib, sys

model_path = pathlib.Path("/app/models/model.json")
if not model_path.exists():
    print("model.json not found, skipping fix")
    sys.exit(0)

data = json.loads(model_path.read_text())

def fix(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "base_score" and isinstance(v, str) and v.startswith("["):
                nums = re.findall(r"[0-9Ee.+\-]+", v)
                node[k] = str(float(nums[0])) if nums else "0.5"
                print(f"Fixed base_score: {v!r} -> {node[k]!r}")
            else:
                fix(v)
    elif isinstance(node, list):
        for item in node: fix(item)

fix(data)
model_path.write_text(json.dumps(data))
print("model.json patched OK")
PYEOF

COPY data/raw/live/ ./data/raw/live/

ENV PORT=8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 120"]
