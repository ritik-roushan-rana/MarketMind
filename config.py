"""Single source of truth for paths, tickers, dates and API settings.

Import this everywhere. Never hardcode a path or a ticker list in a script.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"

PRICES_DIR = RAW / "prices"
NEWS_DIR = RAW / "news"
LIVE_DIR = RAW / "live"

MODELS = ROOT / "models"

ALL_DIRS = [DATA, RAW, INTERIM, PROCESSED, PRICES_DIR, NEWS_DIR, LIVE_DIR, MODELS]

# ---------------------------------------------------------------- universe
# 15 large caps across sectors. Financials are over-weighted on purpose --
# it is a BNP Paribas hackathon.
TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "JPM", "GS", "BAC", "MS",
    "XOM", "JNJ", "WMT", "CAT",
]

BENCHMARK = "SPY"       # market factor
VIX = "^VIX"            # volatility / fear factor

# Everything we need OHLCV for
PRICE_SYMBOLS = TICKERS + [BENCHMARK, VIX]

# ---------------------------------------------------------------- dates
# Finnhub's free tier only reaches back 1 year, so news is the binding
# constraint. Prices go back further so rolling features (SMA50, vol20)
# have a warm-up window before the first labelled day.
PRICE_START = "2023-06-01"
NEWS_LOOKBACK_DAYS = 365

# ---------------------------------------------------------------- finnhub
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"
FINNHUB_SLEEP = 1.1          # free tier is 60 calls/min -- stay under it
FINNHUB_CHUNK_DAYS = 5   # was 30 -- 30-day windows silently truncated for busy tickers
FINNHUB_MAX_RETRIES = 3

# ---------------------------------------------------------------- schema
# Historical collection and live collection MUST both produce exactly these
# columns in this order. If they diverge, train/serve skew follows.
NEWS_SCHEMA = [
    "article_id",      # stable hash, used for dedup
    "ticker",
    "published_utc",   # tz-aware UTC timestamp
    "headline",
    "summary",
    "source",
    "url",
]

PRICE_SCHEMA = [
    "date", "ticker", "open", "high", "low", "close", "volume",
]

# ---------------------------------------------------------------- market time
MARKET_TZ = "America/New_York"
MARKET_CLOSE_HOUR = 16       # 16:00 ET

# ---------------------------------------------------------------- live prices
PRICE_LIVE_LOOKBACK_DAYS = 90   # enough daily bars for SMA50 + buffer
INTRADAY_INTERVAL = "5m"        # granularity for the live chart panel only
INTRADAY_PERIOD = "5d"          # 5m bars stay available for 60 days, 5d is plenty fresh

# Headlines shorter than this are almost always junk ("NVDA", "Market update")
MIN_HEADLINE_CHARS = 20

# ---------------------------------------------------------------- finbert
FINBERT_MODEL = "ProsusAI/finbert"
FINBERT_BATCH_SIZE = 32
FINBERT_MAX_LENGTH = 256

SENTIMENT_CACHE_PATH = INTERIM / "sentiment_cache.parquet"

# article_id is the join key back to news_history.parquet / live snapshots.
# Scores only, never ticker/date -- that way the cache never drifts from
# whatever the news table currently says.
SENTIMENT_SCHEMA = [
    "article_id",
    "sent_positive", "sent_negative", "sent_neutral",
    "sentiment_score",   # p_positive - p_negative, range [-1, 1]
    "confidence",        # 1 - p_neutral
]


# ---------------------------------------------------------------- features
LABEL_BAND_MULT = 0.4       # band = LABEL_BAND_MULT * trailing 20d volatility
SENTIMENT_VOL_WINDOW = 30   # window for the news-count z-score baseline
EMA_HALFLIFE_DAYS = 3

FEATURE_ORDER_PATH = MODELS / "feature_order.json"



# ---------------------------------------------------------------- model
XGB_PARAMS = dict(
    objective="multi:softprob", num_class=3,
    max_depth=4, learning_rate=0.03,
    n_estimators=2000,
    subsample=0.8, colsample_bytree=0.7,
    min_child_weight=10, reg_lambda=3.0, gamma=0.5,
    tree_method="hist", eval_metric="mlogloss",
    early_stopping_rounds=50,
)
CV_N_SPLITS = 4
CV_EMBARGO_DAYS = 1
MODEL_PATH = MODELS / "model.json"
METRICS_PATH = MODELS / "metrics.json"


# ---------------------------------------------------------------- explain
SHAP_TOP_K = 5


# ---------------------------------------------------------------- llm explainer
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"
LLM_MAX_TOKENS = 2048