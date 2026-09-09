"""Runs the full offline feature pipeline: load prices + scored news,
build features, attach labels (both raw-return and excess-return
versions), save to data/processed/.

This is what your training notebook loads from, and it's also the
reference for exactly what the live FastAPI endpoint must reproduce later.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.features.build_features import build_features, save_feature_order, ALL_FEATURE_COLS
from src.features.labels import make_labels, label_balance, add_excess_return_label
from src.features.technical import add_technical_features
from src.sentiment import finbert
from src.utils.io import ensure_dirs, load_parquet, save_parquet

if __name__ == "__main__":
    ensure_dirs()

    prices = load_parquet(config.PRICES_DIR / "prices_daily.parquet")
    news = load_parquet(config.NEWS_DIR / "news_history.parquet")
    news_scored = finbert.join_sentiment(news)

    print(f"prices: {len(prices):,} rows   news: {len(news):,} rows scored\n")

    feats = build_features(prices, news_scored)
    print(f"feature matrix: {feats.shape}")

    priced = add_technical_features(prices)
    labeled_all = make_labels(priced)                    # includes SPY, VIX too
    labeled_all = add_excess_return_label(labeled_all)    # adds fwd_ret_excess, label_excess

    labeled = labeled_all[labeled_all["ticker"].isin(config.TICKERS)][[
        "ticker", "date", "fwd_ret", "label", "label_name",
        "fwd_ret_excess", "label_excess", "label_excess_name",
    ]]

    full = feats.merge(labeled, on=["ticker", "date"], how="left")

    # News only goes back ~1 year while prices go back ~2, so roughly the
    # first year of trading days structurally predate news collection --
    # every one of those rows would show sentiment=0 not because there was
    # no news that day, but because we never collected any for that period.
    # Training on them silently dilutes the sentiment signal and makes the
    # technicals-vs-technicals+sentiment ablation meaningless, since both
    # sides look identical on those rows. Cut to the window where news
    # actually exists, with a 7-day buffer so the first row's 7-day rolling
    # sentiment window isn't itself half-empty by construction.
    news_start = pd.to_datetime(news["published_utc"], utc=True).min().tz_localize(None).normalize()
    cutoff = news_start + pd.Timedelta(days=7)
    print(f"news coverage starts {news_start.date()} -- cutting training rows to "
          f"{cutoff.date()} onward\n")

    full_in_window = full[full["date"] >= cutoff].copy()
    trainable = full_in_window.dropna(subset=["label"]).reset_index(drop=True)

    dropped_pre_news = len(full) - len(full_in_window)
    print(f"dropped {dropped_pre_news:,} rows predating news coverage")
    print(f"trainable rows (labels present, within news window): {len(trainable):,}\n")

    print("label balance, raw target (news-window rows only):")
    print(label_balance(full_in_window).to_string())

    save_parquet(full, config.PROCESSED / "features_all.parquet")
    save_parquet(trainable, config.PROCESSED / "features_trainable.parquet")
    save_feature_order(ALL_FEATURE_COLS)

    print(f"\nsaved -> data/processed/features_trainable.parquet")
    print(f"saved -> models/feature_order.json")