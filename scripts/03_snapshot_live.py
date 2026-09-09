"""Pull a live news snapshot and cache it.

Run this the morning of the demo. If the API or the wifi dies during your
presentation, your dashboard falls back to this file instead of showing an
error in front of the judges.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.collect import news
from src.utils.io import ensure_dirs

if __name__ == "__main__":
    ensure_dirs()
    if not config.FINNHUB_API_KEY:
        sys.exit("FINNHUB_API_KEY not set. See .env.example")

    df = news.snapshot(days=10)
    print(f"\n{len(df):,} articles cached")
    print(news.audit(df).to_string())