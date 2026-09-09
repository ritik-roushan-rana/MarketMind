"""Maps a news timestamp to the trading day it is allowed to influence.

This is the leakage guard. An article published at 18:30 ET on Monday could
not have moved Monday's close -- it belongs to Tuesday. Getting this wrong is
the single most common way a financial ML project produces a fake accuracy
number.

Used by the feature builder, not by collection. It lives here so both the
offline and live path import the identical rule.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config


def assign_market_day(published_utc: pd.Series) -> pd.Series:
    """Return the calendar date each article is attributable to.

    Rule: convert to Eastern time. Anything at or before 16:00 ET belongs to
    that date. Anything after belongs to the next calendar date.

    The result is a calendar date, not necessarily a trading day -- weekends
    and holidays get snapped forward to the next real session later, when you
    join against the price panel.
    """
    ts = pd.to_datetime(published_utc, utc=True)
    et = ts.dt.tz_convert(config.MARKET_TZ)

    after_close = et.dt.hour >= config.MARKET_CLOSE_HOUR
    day = et.dt.normalize()
    day = day.where(~after_close, day + pd.Timedelta(days=1))

    return day.dt.date


def snap_to_sessions(days, sessions) -> pd.Series:
    """Push each calendar date forward to the next actual trading session.

    `sessions` is the sorted array of dates present in your price panel.
    Saturday news lands on Monday, holiday news lands on the next open day.
    """
    days = pd.to_datetime(pd.Series(days))
    sessions = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(sessions)).unique()))
    idx = sessions.searchsorted(days.values, side="left")
    out = pd.Series(pd.NaT, index=days.index, dtype="datetime64[ns]")
    valid = idx < len(sessions)
    out.loc[valid] = sessions[idx[valid]]
    return out