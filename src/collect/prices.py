"""OHLCV collection via yfinance.

Output is one long-format table: date, ticker, open, high, low, close, volume.
Long format keeps the feature builder simple -- one groupby('ticker') and every
rolling window (RSI, SMA, volatility) is correct per ticker.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.utils.io import save_parquet


def _normalize(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """yfinance returns MultiIndex columns in some versions and flat in others.
    Flatten both shapes to the same thing."""
    if raw is None or raw.empty:
        return pd.DataFrame(columns=config.PRICE_SCHEMA)

    df = raw.copy()

    if isinstance(df.columns, pd.MultiIndex):
        lv0 = set(df.columns.get_level_values(0))
        if ticker in lv0:
            df = df.xs(ticker, axis=1, level=0)
        else:
            df = df.xs(ticker, axis=1, level=1)

    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    df = df.reset_index()

    date_col = "date" if "date" in df.columns else df.columns[0]
    df = df.rename(columns={date_col: "date"})

    # strip timezone -- these are daily bars, the time component is noise
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["ticker"] = ticker

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[config.PRICE_SCHEMA]
    df = df.dropna(subset=["close"])
    return df.sort_values("date").reset_index(drop=True)


def fetch_symbol(ticker: str, start: str, end: str = None) -> pd.DataFrame:
    """Download one symbol. auto_adjust=True gives split/dividend adjusted
    closes, which is what you want for return calculations."""
    raw = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    return _normalize(raw, ticker)


def fetch_panel(
    symbols: list = None,
    start: str = None,
    end: str = None,
    pause: float = 0.4,
) -> pd.DataFrame:
    """Download every symbol and stack into one panel."""
    symbols = symbols or config.PRICE_SYMBOLS
    start = start or config.PRICE_START

    frames, failed = [], []
    for i, sym in enumerate(symbols, 1):
        try:
            df = fetch_symbol(sym, start, end)
            if df.empty:
                failed.append(sym)
                print(f"  [{i}/{len(symbols)}] {sym:<6} EMPTY")
            else:
                frames.append(df)
                print(f"  [{i}/{len(symbols)}] {sym:<6} {len(df):>5} rows  "
                      f"{df['date'].min().date()} -> {df['date'].max().date()}")
        except Exception as exc:
            failed.append(sym)
            print(f"  [{i}/{len(symbols)}] {sym:<6} FAILED: {exc}")
        time.sleep(pause)

    if failed:
        print(f"\n  warning: no data for {failed}")
    if not frames:
        raise RuntimeError("no price data collected -- check your connection")

    panel = pd.concat(frames, ignore_index=True)
    return panel.sort_values(["ticker", "date"]).reset_index(drop=True)


def audit(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker sanity table. Look at this before moving on."""
    g = panel.groupby("ticker")
    out = pd.DataFrame({
        "rows": g.size(),
        "first": g["date"].min().dt.date,
        "last": g["date"].max().dt.date,
        "null_close": g["close"].apply(lambda s: s.isna().sum()),
        "zero_volume_days": g["volume"].apply(lambda s: (s == 0).sum()),
    })
    return out.sort_values("rows")


def save(panel: pd.DataFrame) -> Path:
    return save_parquet(panel, config.PRICES_DIR / "prices_daily.parquet")

def fetch_live_panel_fast(symbols: list = None, lookback_days: int = None) -> pd.DataFrame:
    """Same output as fetch_live_panel(), but ONE batched network call
    instead of 17 sequential ones with sleeps between them.

    fetch_panel()/fetch_live_panel() loop per-symbol because that's safe
    for a one-time 2-year historical backfill where a single bad ticker
    shouldn't kill the whole run. For a live request that a user is
    waiting on, 17 sequential round-trips is the difference between a
    fast demo and a 30-second stall -- batch it instead.
    """
    symbols = symbols or config.PRICE_SYMBOLS
    lookback_days = lookback_days or config.PRICE_LIVE_LOOKBACK_DAYS
    start = (pd.Timestamp.today() - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    raw = yf.download(
        symbols, start=start, auto_adjust=True,
        progress=False, threads=True, group_by="ticker",
    )

    frames = []
    for sym in symbols:
        try:
            sub = raw[sym] if isinstance(raw.columns, pd.MultiIndex) else raw
        except KeyError:
            continue
        df = _normalize(sub, sym)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("batched live price fetch returned no data")

    panel = pd.concat(frames, ignore_index=True)
    return panel.sort_values(["ticker", "date"]).reset_index(drop=True)

def _normalize_intraday(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Separate from _normalize() on purpose -- that one collapses to a
    calendar date, which would destroy intraday timestamps."""
    cols = ["timestamp", "ticker", "open", "high", "low", "close", "volume"]
    if raw is None or raw.empty:
        return pd.DataFrame(columns=cols)

    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        lv0 = set(df.columns.get_level_values(0))
        df = df.xs(ticker, axis=1, level=0) if ticker in lv0 else df.xs(ticker, axis=1, level=1)

    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    df = df.reset_index()

    ts_col = "datetime" if "datetime" in df.columns else df.columns[0]
    df = df.rename(columns={ts_col: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ticker"] = ticker

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[cols].dropna(subset=["close"])
    return df.sort_values("timestamp").reset_index(drop=True)


def fetch_intraday(ticker: str, period: str = None, interval: str = None) -> pd.DataFrame:
    """Recent intraday bars for the live chart panel only -- this feeds the
    UI, not the model. The model's features are all daily. yfinance intraday
    data is delayed ~15 minutes on the free tier, fine for a dashboard, not
    fine for real trading."""
    period = period or config.INTRADAY_PERIOD
    interval = interval or config.INTRADAY_INTERVAL
    raw = yf.download(ticker, period=period, interval=interval,
                       auto_adjust=True, progress=False, threads=False)
    return _normalize_intraday(raw, ticker)


def snapshot(symbols: list = None, lookback_days: int = None) -> pd.DataFrame:
    """Cache a live daily panel to disk. Run this the morning of the demo so
    you have a fallback if the venue wifi or yfinance is down mid-presentation."""
    panel = fetch_live_panel(symbols, lookback_days)
    stamp = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M")
    save_parquet(panel, config.LIVE_DIR / f"prices_snapshot_{stamp}.parquet")
    save_parquet(panel, config.LIVE_DIR / "prices_snapshot_latest.parquet")
    return panel