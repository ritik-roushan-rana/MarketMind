"""Purged walk-forward cross-validation for panel (ticker x date) data.

Rows are (ticker, date) pairs, so a plain random K-fold would put e.g.
NVDA on 2026-03-11 in train and AAPL on 2026-03-11 in validation --
information from the same trading day leaking across the split via a
shared market factor (SPY, VIX). Splitting must happen on the DATE axis
only; all tickers move together into train or into val as a block.

Embargo: the label for day t looks at close(t) -> close(t+1). Letting
train end on day t and val start on day t+1 puts adjacent, highly
correlated days on either side of the boundary, so `embargo_days` worth
of dates are dropped between every train/val split.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def purged_walk_forward_splits(dates, n_splits: int = 4, embargo_days: int = 1):
    """
    dates : the full set of trading dates present in the dataset (can have
            duplicates, e.g. one per ticker -- this function uniques them).

    Yields (train_dates, val_dates) as numpy datetime64 arrays, expanding
    window: fold i trains on everything before its validation block.
    Validation blocks are contiguous and non-overlapping across folds.
    """
    uniq = np.array(sorted(pd.to_datetime(pd.Series(dates)).unique()))
    n = len(uniq)
    if n < n_splits * 2:
        raise ValueError(f"only {n} unique dates -- too few for {n_splits} splits")

    warm = max(int(n * 0.35), 5)
    remaining = n - warm
    block_size = max(remaining // n_splits, 1)

    for i in range(n_splits):
        val_start_idx = warm + i * block_size
        val_end_idx = warm + (i + 1) * block_size if i < n_splits - 1 else n
        if val_start_idx >= n:
            break
        val_dates = uniq[val_start_idx:val_end_idx]

        train_end_idx = max(val_start_idx - embargo_days, 1)
        train_dates = uniq[:train_end_idx]

        if len(train_dates) == 0 or len(val_dates) == 0:
            continue

        yield train_dates, val_dates