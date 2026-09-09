"""Create the folder tree and check your environment. Run this first."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.utils.io import ensure_dirs

if __name__ == "__main__":
    dirs = ensure_dirs()
    print("directories ready:")
    for d in dirs:
        print(f"  {d.relative_to(config.ROOT)}")

    print(f"\ntickers      : {len(config.TICKERS)}")
    print(f"price start  : {config.PRICE_START}")
    print(f"news lookback: {config.NEWS_LOOKBACK_DAYS} days")

    key = config.FINNHUB_API_KEY
    if key:
        print(f"finnhub key  : set ({key[:6]}...)")
    else:
        print("finnhub key  : MISSING")
        print("               copy .env.example to .env and paste your free key")