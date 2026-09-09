"""Download the OHLCV panel. Takes about a minute. No API key needed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.collect import prices
from src.utils.io import ensure_dirs

if __name__ == "__main__":
    ensure_dirs()

    print(f"downloading {len(config.PRICE_SYMBOLS)} symbols from {config.PRICE_START}\n")
    panel = prices.fetch_panel()

    print("\naudit:")
    print(prices.audit(panel).to_string())

    path = prices.save(panel)
    print(f"\nsaved {len(panel):,} rows -> {path.relative_to(config.ROOT)}")
    print(f"sessions: {panel['date'].nunique()}  tickers: {panel['ticker'].nunique()}")