"""The one function both the offline training path and the live serving
path call. If this function's output ever differs between the two callers,
the model sees different inputs than it was trained on -- train/serve skew.

Given raw prices (all symbols, including SPY/VIX) and sentiment-scored news,
returns one row per (ticker, trading day) with every model feature, ready
for XGBoost. Does NOT attach labels -- that only makes sense for the
training path, since live rows have no "tomorrow" yet. Call labels.py
separately, only when training.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.features.technical import add_technical_features, TECHNICAL_FEATURE_COLS
from src.features.sentiment_features import build_sentiment_features, SENTIMENT_FEATURE_COLS

MARKET_FEATURE_COLS = ["spy_ret_1d", "vix_level", "vix_change_1d", "day_of_week"]

ALL_FEATURE_COLS = TECHNICAL_FEATURE_COLS + SENTIMENT_FEATURE_COLS + MARKET_FEATURE_COLS


def _market_context(price_with_technicals: pd.DataFrame) -> pd.DataFrame:
    """SPY and VIX aren't tickers we predict -- they're context columns
    joined onto every ticker's row for the same date."""
    spy = price_with_technicals[price_with_technicals["ticker"] == config.BENCHMARK]
    spy = spy[["date", "ret_1d"]].rename(columns={"ret_1d": "spy_ret_1d"})

    vix = price_with_technicals[price_with_technicals["ticker"] == config.VIX]
    vix = vix[["date", "close", "ret_1d"]].rename(
        columns={"close": "vix_level", "ret_1d": "vix_change_1d"}
    )

    ctx = spy.merge(vix, on="date", how="outer").sort_values("date")
    return ctx


def build_features(
    price_panel: pd.DataFrame,
    news_scored: pd.DataFrame,
    tickers: list = None,
) -> pd.DataFrame:
    """
    price_panel : long format, date/ticker/open/high/low/close/volume,
                  for ALL symbols (tickers + SPY + VIX).
    news_scored : news joined with FinBERT scores (see
                  src/sentiment/finbert.join_sentiment), any date range.
    tickers     : which symbols to produce feature ROWS for. Defaults to
                  config.TICKERS -- SPY/VIX are context only, never rows.

    Returns one row per (ticker, date) with every column in ALL_FEATURE_COLS,
    plus identifying columns ticker/date/close (close kept for convenience
    when computing labels or displaying predictions downstream).
    """
    tickers = tickers or config.TICKERS

    priced = add_technical_features(price_panel)
    ctx = _market_context(priced)

    sessions_by_ticker = {
        t: pd.DatetimeIndex(sorted(priced.loc[priced["ticker"] == t, "date"].unique()))
        for t in tickers
    }

    sentiment = build_sentiment_features(news_scored, sessions_by_ticker)

    rows = priced[priced["ticker"].isin(tickers)].copy()
    rows = rows.merge(sentiment, on=["ticker", "date"], how="left")
    rows = rows.merge(ctx, on="date", how="left")

    rows["day_of_week"] = pd.to_datetime(rows["date"]).dt.dayofweek

    for col in SENTIMENT_FEATURE_COLS:
        rows[col] = rows[col].fillna(0)

    keep = ["ticker", "date", "close"] + ALL_FEATURE_COLS
    return rows[keep].reset_index(drop=True)


def save_feature_order(cols: list = None) -> Path:
    """Write the exact column order used at train time. The live path loads
    this and must build its DataFrame in the identical order before calling
    model.predict() -- XGBoost has no column names at inference, only
    position, so an order mismatch fails silently and just gives wrong
    predictions instead of an error."""
    import json
    cols = cols or ALL_FEATURE_COLS
    config.MODELS.mkdir(parents=True, exist_ok=True)
    with open(config.FEATURE_ORDER_PATH, "w") as f:
        json.dump(cols, f, indent=2)
    return config.FEATURE_ORDER_PATH