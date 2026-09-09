"""Tiny in-memory TTL cache for the live price panel and per-ticker news.

Refetching all 17 symbols and hitting Finnhub on every single /predict
call is wasteful and slow. Prices and headlines don't meaningfully change
faster than a few minutes, matching the earlier design decision: live
sentiment refreshes every ~15 min, the model's horizon is next-day close.
This also makes repeated demo clicks across tickers fast after the first
one warms the cache.
"""
import time

_PRICE_CACHE = {"data": None, "ts": 0.0}
_NEWS_CACHE: dict = {}

PRICE_TTL_SECONDS = 300   # 5 min
NEWS_TTL_SECONDS = 300    # 5 min


def get_cached_price_panel(fetch_fn):
    now = time.time()
    if _PRICE_CACHE["data"] is not None and (now - _PRICE_CACHE["ts"]) < PRICE_TTL_SECONDS:
        return _PRICE_CACHE["data"]
    data = fetch_fn()
    _PRICE_CACHE["data"] = data
    _PRICE_CACHE["ts"] = now
    return data


def get_cached_news(ticker: str, fetch_fn):
    now = time.time()
    entry = _NEWS_CACHE.get(ticker)
    if entry is not None and (now - entry["ts"]) < NEWS_TTL_SECONDS:
        return entry["data"]
    data = fetch_fn()
    _NEWS_CACHE[ticker] = {"data": data, "ts": now}
    return data