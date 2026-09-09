"""The live counterpart to scripts 06-09: fetches fresh news + prices for
ONE ticker, runs them through the exact same build_features() used in
training, predicts with the already-trained model, and explains the result
with SHAP + the LLM.

This function is the entire reason build_features() was written as a
single shared function back in Part 1 -- every step here reuses code
that was tested against historical data, unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.collect import news as news_collect
from src.collect import prices as price_collect
from src.features.build_features import build_features
from src.model.explain import LABEL_NAMES, explain_row, format_for_llm
from src.model.llm_explainer import explain as llm_explain
from src.sentiment import finbert
from src.utils.io import load_parquet
from api.services.cache import get_cached_news, get_cached_price_panel


class PredictionError(RuntimeError):
    pass

def _live_data(ticker: str):
    """Fetch fresh news + prices (through a short TTL cache so repeated
    calls are fast), falling back to the demo-day snapshot if the live
    fetch fails entirely."""
    warning = None
    try:
        news = get_cached_news(ticker, lambda: news_collect.fetch_live(ticker))
        prices = get_cached_price_panel(price_collect.fetch_live_panel_fast)
    except Exception as exc:
        warning = f"live fetch failed ({exc.__class__.__name__}), using cached snapshot"
        news_path = config.LIVE_DIR / "news_snapshot_latest.parquet"
        prices_path = config.LIVE_DIR / "prices_snapshot_latest.parquet"
        if not news_path.exists() or not prices_path.exists():
            raise PredictionError(
                "live fetch failed and no cached snapshot exists -- "
                "run scripts/03_snapshot_live.py and "
                "scripts/04_snapshot_live_prices.py first"
            ) from exc
        news = load_parquet(news_path)
        news = news[news["ticker"] == ticker]
        prices = load_parquet(prices_path)

    return news, prices, warning

def predict_ticker(ticker: str, model, feature_cols: list, explainer) -> dict:
    """Returns a plain dict matching api.schemas.PredictionResponse's
    fields -- kept as a dict rather than the pydantic model itself so this
    function has no FastAPI dependency and can be unit tested standalone.
    """
    if ticker not in config.TICKERS:
        raise PredictionError(f"'{ticker}' is not in the supported ticker list")

    news, prices, warning = _live_data(ticker)
    news_scored = finbert.join_sentiment(news) if not news.empty else news.assign(sentiment_score=[])

    if news_scored.empty or news_scored["sentiment_score"].isna().all():
        news_scored = finbert.update_cache(news) if not news.empty else news
        news_scored = finbert.join_sentiment(news) if not news.empty else news

    feats = build_features(prices, news_scored, tickers=[ticker])
    if feats.empty:
        raise PredictionError(f"no feature rows produced for {ticker} -- check live data")

    row = feats.sort_values("date").iloc[-1]
    X = row[feature_cols].values.astype(float).reshape(1, -1)

    proba = model.predict_proba(X)[0]
    pred_class = int(proba.argmax())

    class_probabilities = {LABEL_NAMES[i]: float(p) for i, p in enumerate(proba)}
    contrib = explain_row(explainer, row, feature_cols, pred_class)

    recent_headlines = []
    if not news.empty:
        recent_headlines = (
            news.sort_values("published_utc", ascending=False)["headline"].head(3).tolist()
        )

    prompt_text = format_for_llm(
        ticker, row["date"].date() if hasattr(row["date"], "date") else row["date"],
        pred_class, proba[pred_class], contrib, headlines=recent_headlines,
    )

    try:
        explanation_text = llm_explain(prompt_text)
    except Exception as exc:
        explanation_text = (
            f"(explanation unavailable: {exc.__class__.__name__} -- "
            f"showing raw model output instead)"
        )

    return dict(
        ticker=ticker,
        as_of_date=str(row["date"].date() if hasattr(row["date"], "date") else row["date"]),
        predicted_label=LABEL_NAMES[pred_class],
        predicted_proba=float(proba[pred_class]),
        class_probabilities=class_probabilities,
        top_drivers=[
            {"feature": r["feature"], "value": float(r["value"]), "shap": float(r["shap"])}
            for _, r in contrib.iterrows()
        ],
        explanation=explanation_text,
        headlines_used=recent_headlines,
        warning=warning,
    )