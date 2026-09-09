"""Backfill one year of company news. Needs FINNHUB_API_KEY.

Roughly 15 tickers x 13 monthly chunks x 1.1s = about 4 minutes.
Resumable -- if it dies, just run it again.
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

    print(f"backfilling {config.NEWS_LOOKBACK_DAYS} days for "
          f"{len(config.TICKERS)} tickers\n")
    df = news.backfill()

    print("\naudit:")
    print(news.audit(df).to_string())
    print(f"\ntotal: {len(df):,} articles -> data/raw/news/news_history.parquet")