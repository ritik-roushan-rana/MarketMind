"""News collection from Finnhub.

Two entry points, ONE normalizer:

    fetch_history(ticker, days)  -> offline backfill, chunked by month
    fetch_live(ticker, days)     -> what the dashboard calls every 15 min

Both return exactly config.NEWS_SCHEMA. That is deliberate. The moment the
live path produces a different shape from the training path, your model is
seeing features it was never trained on and the predictions become garbage in
a way that is very hard to debug.
"""
from __future__ import annotations

import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.utils.io import append_parquet, hash_id, save_parquet


class FinnhubError(RuntimeError):
    pass


def _get(endpoint: str, params: dict) -> list:
    """One Finnhub GET with retry and rate-limit backoff."""
    if not config.FINNHUB_API_KEY:
        raise FinnhubError(
            "FINNHUB_API_KEY is not set. Get a free key at finnhub.io/register "
            "and put it in your .env file."
        )

    params = {**params, "token": config.FINNHUB_API_KEY}
    url = f"{config.FINNHUB_BASE}/{endpoint}"

    for attempt in range(config.FINNHUB_MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=30)
        except requests.exceptions.RequestException as exc:
            wait = 3 * (attempt + 1)
            print(f"    network error ({exc.__class__.__name__}), retrying in {wait}s")
            time.sleep(wait)
            continue

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:              # rate limited
            wait = 5 * (attempt + 1)
            print(f"    rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        if resp.status_code in (401, 403):
            raise FinnhubError(f"auth failed ({resp.status_code}) -- check your API key")
        time.sleep(2 * (attempt + 1))

    raise FinnhubError(f"{endpoint} failed after {config.FINNHUB_MAX_RETRIES} attempts")


# ------------------------------------------------------------------ normalize
def normalize(records: list, ticker: str) -> pd.DataFrame:
    """Raw Finnhub JSON -> config.NEWS_SCHEMA. The only place that maps the
    vendor's field names onto ours."""
    if not records:
        return pd.DataFrame(columns=config.NEWS_SCHEMA)

    rows = []
    for r in records:
        headline = (r.get("headline") or "").strip()
        if len(headline) < config.MIN_HEADLINE_CHARS:
            continue

        ts = r.get("datetime")
        if not ts:
            continue

        url = (r.get("url") or "").strip()
        rows.append({
            "article_id": hash_id(url or headline, ticker),
            "ticker": ticker,
            "published_utc": pd.to_datetime(ts, unit="s", utc=True),
            "headline": headline,
            "summary": (r.get("summary") or "").strip(),
            "source": (r.get("source") or "unknown").strip(),
            "url": url,
        })

    if not rows:
        return pd.DataFrame(columns=config.NEWS_SCHEMA)

    df = pd.DataFrame(rows)[config.NEWS_SCHEMA]
    return df.drop_duplicates(subset=["article_id"]).reset_index(drop=True)


# ------------------------------------------------------------------ history
def _month_chunks(start: date, end: date, size: int):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=size), end)
        yield cur, nxt
        cur = nxt


def fetch_history(ticker: str, days: int | None = None, verbose: bool = True) -> pd.DataFrame:
    """Backfill one ticker. Chunked because company-news silently truncates
    long date ranges -- ask for a year in one call and you get a few hundred
    of the most recent articles, not the year."""
    days = days or config.NEWS_LOOKBACK_DAYS
    end = date.today()
    start = end - timedelta(days=days)

    frames = []
    for a, b in _month_chunks(start, end, config.FINNHUB_CHUNK_DAYS):
        recs = _get("company-news", {
            "symbol": ticker,
            "from": a.isoformat(),
            "to": b.isoformat(),
        })
        df = normalize(recs, ticker)
        frames.append(df)
        if verbose:
            print(f"    {a} -> {b}: {len(df):>4} articles")
        time.sleep(config.FINNHUB_SLEEP)

    if not frames:
        return pd.DataFrame(columns=config.NEWS_SCHEMA)

    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["article_id"])
    return out.sort_values("published_utc").reset_index(drop=True)


def backfill(tickers: list[str] | None = None, days: int | None = None) -> pd.DataFrame:
    """Backfill every ticker, saving after each one so a crash is cheap."""
    tickers = tickers or config.TICKERS
    path = config.NEWS_DIR / "news_history.parquet"

    for i, t in enumerate(tickers, 1):
        print(f"  [{i}/{len(tickers)}] {t}")
        try:
            df = fetch_history(t, days)
        except FinnhubError as exc:
            print(f"    FAILED: {exc}")
            continue
        if df.empty:
            print("    no articles")
            continue
        append_parquet(df, path, dedup_on="article_id")
        print(f"    +{len(df)} articles saved")

    return pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=config.NEWS_SCHEMA)


# ------------------------------------------------------------------ live
def fetch_live(ticker: str, days: int = 10) -> pd.DataFrame:
    """What the dashboard calls. Same normalizer, same schema.

    days=10 rather than 1 because your rolling sentiment features need a
    7-day window -- "live" means "recent window ending now", not "this
    instant".
    """
    end = date.today()
    start = end - timedelta(days=days)
    recs = _get("company-news", {
        "symbol": ticker,
        "from": start.isoformat(),
        "to": end.isoformat(),
    })
    return normalize(recs, ticker).sort_values("published_utc").reset_index(drop=True)


def snapshot(tickers: list[str] | None = None, days: int = 10) -> pd.DataFrame:
    """Cache a live pull to disk. Run this the morning of the demo so you have
    a fallback if the venue wifi or the API dies mid-presentation."""
    tickers = tickers or config.TICKERS
    frames = []
    for t in tickers:
        try:
            frames.append(fetch_live(t, days))
        except FinnhubError as exc:
            print(f"  {t}: {exc}")
        time.sleep(config.FINNHUB_SLEEP)

    out = (pd.concat(frames, ignore_index=True) if frames
           else pd.DataFrame(columns=config.NEWS_SCHEMA))
    stamp = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M")
    save_parquet(out, config.LIVE_DIR / f"news_snapshot_{stamp}.parquet")
    save_parquet(out, config.LIVE_DIR / "news_snapshot_latest.parquet")
    return out


# ------------------------------------------------------------------ audit
def audit(news: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker coverage. Thin tickers are a real finding, not a bug --
    but you need to know which ones before you train."""
    if news.empty:
        return pd.DataFrame()
    n = news.copy()
    n["day"] = pd.to_datetime(n["published_utc"], utc=True).dt.date
    g = n.groupby("ticker")
    out = pd.DataFrame({
        "articles": g.size(),
        "days_covered": g["day"].nunique(),
        "first": g["published_utc"].min().dt.date,
        "last": g["published_utc"].max().dt.date,
        "sources": g["source"].nunique(),
    })
    out["articles_per_day"] = (out["articles"] / out["days_covered"]).round(1)
    return out.sort_values("articles")