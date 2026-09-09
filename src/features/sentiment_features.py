"""Article-level sentiment scores -> per (ticker, trading day) rolling
features.

This is the piece that turns "14 separate FinBERT scores on Tuesday" into
one row's worth of sentiment_mean_3d, sentiment_mean_7d, news_count_zscore,
etc. Everything here is trailing-only, same rule as technical.py.

Days with zero articles are represented explicitly (count=0), not dropped --
a ticker going quiet is itself a signal, and rolling windows need the full
trading calendar to mean the right thing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.utils.market_time import assign_market_day, snap_to_sessions


def _daily_buckets(news_scored: pd.DataFrame) -> pd.DataFrame:
    """Collapse articles to one row per (ticker, published day), summed --
    sums instead of means so reindexing/rolling never has to juggle NaNs."""
    n = news_scored.dropna(subset=["sentiment_score"]).copy()
    n["market_day"] = assign_market_day(n["published_utc"])
    n["is_negative"] = (n["sentiment_score"] < -0.3).astype(int)

    g = n.groupby(["ticker", "market_day"])
    daily = g.agg(
        score_sum=("sentiment_score", "sum"),
        article_count=("sentiment_score", "count"),
        neg_count=("is_negative", "sum"),
    ).reset_index()
    daily["market_day"] = pd.to_datetime(daily["market_day"])
    return daily


def _reindex_to_sessions(daily: pd.DataFrame, ticker: str, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Snap each article's market_day onto the ticker's real trading
    sessions (weekends/holidays roll forward), then reindex to every
    session so no-news days appear as explicit zero rows."""
    t = daily[daily["ticker"] == ticker].copy()
    if not t.empty:
        t["date"] = snap_to_sessions(t["market_day"], sessions)
        t = t.groupby("date", as_index=False)[["score_sum", "article_count", "neg_count"]].sum()

    full = pd.DataFrame({"date": sessions})
    full = full.merge(t, on="date", how="left")
    full[["score_sum", "article_count", "neg_count"]] = (
        full[["score_sum", "article_count", "neg_count"]].fillna(0)
    )
    full["ticker"] = ticker
    return full.sort_values("date").reset_index(drop=True)


def _rolling_ratio(sum_col: pd.Series, count_col: pd.Series, window: int) -> pd.Series:
    roll_sum = sum_col.rolling(window, min_periods=1).sum()
    roll_count = count_col.rolling(window, min_periods=1).sum()
    return (roll_sum / roll_count.replace(0, np.nan)).fillna(0)


def _one_ticker_sentiment(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("date").copy()

    g["sentiment_mean_1d"] = _rolling_ratio(g["score_sum"], g["article_count"], 1)
    g["sentiment_mean_3d"] = _rolling_ratio(g["score_sum"], g["article_count"], 3)
    g["sentiment_mean_7d"] = _rolling_ratio(g["score_sum"], g["article_count"], 7)

    g["news_count_1d"] = g["article_count"]
    g["news_count_3d"] = g["article_count"].rolling(3, min_periods=1).sum()
    g["news_count_7d"] = g["article_count"].rolling(7, min_periods=1).sum()

    g["negativity_share_7d"] = _rolling_ratio(g["neg_count"], g["article_count"], 7)

    roll_mean = g["news_count_1d"].rolling(config.SENTIMENT_VOL_WINDOW, min_periods=5).mean()
    roll_std = g["news_count_1d"].rolling(config.SENTIMENT_VOL_WINDOW, min_periods=5).std()
    g["news_count_zscore"] = ((g["news_count_1d"] - roll_mean) / roll_std.replace(0, np.nan)).fillna(0)

    daily_mean = (g["score_sum"] / g["article_count"].replace(0, np.nan)).fillna(0)
    g["sentiment_ema_3d"] = daily_mean.ewm(halflife=config.EMA_HALFLIFE_DAYS, min_periods=1).mean()
    g["sentiment_momentum"] = daily_mean.diff(1).fillna(0)

    return g


def build_sentiment_features(news_scored: pd.DataFrame, sessions_by_ticker: dict) -> pd.DataFrame:
    """sessions_by_ticker: {ticker: sorted DatetimeIndex of that ticker's
    real trading days}, taken from the price panel so the sentiment
    calendar always matches the price calendar exactly."""
    daily = _daily_buckets(news_scored)

    frames = []
    for ticker, sessions in sessions_by_ticker.items():
        full = _reindex_to_sessions(daily, ticker, sessions)
        frames.append(_one_ticker_sentiment(full))

    out = pd.concat(frames, ignore_index=True)
    return out[[
        "ticker", "date",
        "sentiment_mean_1d", "sentiment_mean_3d", "sentiment_mean_7d",
        "news_count_1d", "news_count_3d", "news_count_7d",
        "negativity_share_7d", "news_count_zscore",
        "sentiment_ema_3d", "sentiment_momentum",
    ]]


SENTIMENT_FEATURE_COLS = [
    "sentiment_mean_1d", "sentiment_mean_3d", "sentiment_mean_7d",
    "news_count_1d", "news_count_3d", "news_count_7d",
    "negativity_share_7d", "news_count_zscore",
    "sentiment_ema_3d", "sentiment_momentum",
]