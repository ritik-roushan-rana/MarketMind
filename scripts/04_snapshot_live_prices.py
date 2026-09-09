"""Pull a live daily price panel and cache it.

Run this the morning of the demo. Same idea as 03_snapshot_live.py for news --
if yfinance or the wifi flakes out mid-presentation, the dashboard falls back
to this file instead of erroring in front of the judges.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.collect import prices
from src.utils.io import ensure_dirs

if __name__ == "__main__":
    ensure_dirs()

    panel = prices.snapshot()
    print(f"cached {len(panel):,} rows")
    print(prices.audit(panel).to_string())