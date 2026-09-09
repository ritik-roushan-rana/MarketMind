"""Volatility-scaled three-class label: up / flat / down.

Plain next-day direction is close to a coin flip and mostly encodes market
drift. Scaling the threshold by each ticker's own trailing volatility means
a quiet stock (utilities) and a wild one (a momentum name) both need a
"real" move relative to their own normal noise, not the same fixed percent.

Uses vol_20d, a TRAILING technical feature already computed as of day t --
not a rolling std of the forward return -- so the label threshold itself
introduces no lookahead.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config


def _one_ticker_labels(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("date").copy()

    close = g["close"]
    g["fwd_ret"] = close.shift(-1) / close - 1          # close(t) -> close(t+1)
    band = config.LABEL_BAND_MULT * g["vol_20d"]

    conditions = [
        g["fwd_ret"] > band,
        g["fwd_ret"] < -band,
    ]
    g["label"] = np.select(conditions, [1, 2], default=0)   # 0 flat, 1 up, 2 down
    g["label_name"] = g["label"].map({0: "flat", 1: "up", 2: "down"})

    # last row has no fwd_ret (no tomorrow yet) and early rows have no
    # vol_20d (rolling window not full) -- both are unusable for training
    g.loc[g["fwd_ret"].isna() | g["vol_20d"].isna(), ["label", "label_name"]] = [np.nan, None]

    return g


def make_labels(price_with_technicals: pd.DataFrame) -> pd.DataFrame:
    """price_with_technicals must already have vol_20d from technical.py.
    Adds fwd_ret, label (0/1/2), label_name. Rows with label NaN are not
    trainable -- drop them before handing off to XGBoost.

    Explicit loop, not groupby.apply -- see the comment in technical.py's
    add_technical_features for why.
    """
    frames = []
    for ticker, g in price_with_technicals.groupby("ticker"):
        g = _one_ticker_labels(g)
        g["ticker"] = ticker
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def label_balance(labeled: pd.DataFrame) -> pd.DataFrame:
    """Sanity check: class counts should be roughly balanced, not
    dominated by one class. If "flat" is >70%, LABEL_BAND_MULT is too wide."""
    valid = labeled.dropna(subset=["label"])
    counts = valid["label_name"].value_counts()
    pct = (100 * counts / len(valid)).round(1)
    return pd.DataFrame({"count": counts, "pct": pct})


def add_excess_return_label(labeled_all: pd.DataFrame, benchmark: str = None) -> pd.DataFrame:
    """Excess-return version of the label: subtract the benchmark's forward
    return before applying the SAME volatility band used for the raw label.
    Isolates stock-specific movement from market-wide drift -- the
    component sentiment would most plausibly explain, if it explains
    anything at all.

    Adds fwd_ret_excess / label_excess / label_excess_name as NEW columns
    alongside the existing raw-return label, rather than replacing it, so
    the two can be compared under an otherwise identical setup: same
    XGBoost config, same CV splits, same features -- only the target
    changes.

    labeled_all must be the output of make_labels() run on the FULL price
    panel (including the benchmark ticker itself, not pre-filtered to your
    prediction universe) -- we need the benchmark's own fwd_ret to subtract.
    """
    benchmark = benchmark or config.BENCHMARK
    bench = labeled_all[labeled_all["ticker"] == benchmark][["date", "fwd_ret"]]
    bench = bench.rename(columns={"fwd_ret": "bench_fwd_ret"})

    out = labeled_all.merge(bench, on="date", how="left")
    out["fwd_ret_excess"] = out["fwd_ret"] - out["bench_fwd_ret"]

    band = config.LABEL_BAND_MULT * out["vol_20d"]
    conditions = [out["fwd_ret_excess"] > band, out["fwd_ret_excess"] < -band]
    out["label_excess"] = np.select(conditions, [1, 2], default=0)
    out["label_excess_name"] = out["label_excess"].map({0: "flat", 1: "up", 2: "down"})

    invalid = out["fwd_ret_excess"].isna() | out["vol_20d"].isna()
    out.loc[invalid, ["label_excess", "label_excess_name"]] = [np.nan, None]

    return out.drop(columns=["bench_fwd_ret"])