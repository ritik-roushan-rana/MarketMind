"""Technical indicators, computed independently per ticker.

Every function here is trailing-only: a value at row t uses only data up to
and including day t. That's what makes them safe to use as features -- no
future information leaks in, so no shift() is needed on this side (the
label, not the features, is where the forward-looking step happens).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # flat price history -> neutral RSI, not NaN


def _macd_hist(close: pd.Series, fast=12, slow=26, signal=9) -> pd.Series:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd - signal_line


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def _one_ticker(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("date").copy()
    close, high, low, volume = g["close"], g["high"], g["low"], g["volume"]

    g["ret_1d"] = close.pct_change(1)
    g["ret_3d"] = close.pct_change(3)
    g["ret_5d"] = close.pct_change(5)
    g["ret_10d"] = close.pct_change(10)

    g["vol_5d"] = g["ret_1d"].rolling(5).std()
    g["vol_20d"] = g["ret_1d"].rolling(20).std()

    g["rsi_14"] = _rsi(close, 14)
    g["macd_hist"] = _macd_hist(close)
    g["atr_ratio"] = _atr(high, low, close) / close

    vol_ma20 = volume.rolling(20).mean()
    g["volume_ratio"] = volume / vol_ma20.replace(0, np.nan)

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    g["sma20_dist"] = (close - sma20) / sma20
    g["sma50_dist"] = (close - sma50) / sma50

    return g


def add_technical_features(price_panel: pd.DataFrame) -> pd.DataFrame:
    """price_panel: long format, columns date/ticker/open/high/low/close/volume,
    for ALL symbols including SPY and VIX. Returns the same panel with
    technical columns appended, still long format, still every symbol.

    Uses an explicit loop rather than groupby.apply -- pandas changed
    whether the grouping column survives inside apply() between versions
    (a FutureWarning on 2.x, a hard break on 3.x), so looping avoids
    depending on that behavior at all.
    """
    frames = []
    for ticker, g in price_panel.groupby("ticker"):
        g = _one_ticker(g)
        g["ticker"] = ticker
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


TECHNICAL_FEATURE_COLS = [
    "ret_1d", "ret_3d", "ret_5d", "ret_10d",
    "vol_5d", "vol_20d",
    "rsi_14", "macd_hist", "atr_ratio",
    "volume_ratio", "sma20_dist", "sma50_dist",
]