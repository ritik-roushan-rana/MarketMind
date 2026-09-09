"""Small IO helpers. Parquet everywhere -- it preserves dtypes and timezones,
CSV does not."""
import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config


def ensure_dirs():
    """Create every directory the project expects. Safe to run repeatedly."""
    for d in config.ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    return config.ALL_DIRS


def save_parquet(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path))


def append_parquet(df: pd.DataFrame, path: Path, dedup_on: str) -> pd.DataFrame:
    """Merge new rows into an existing parquet, dropping duplicates.

    This is what makes collection resumable -- if a run dies halfway through,
    rerunning it costs you nothing but the missing tickers.
    """
    path = Path(path)
    if path.exists():
        old = load_parquet(path)
        df = pd.concat([old, df], ignore_index=True)
    df = df.drop_duplicates(subset=[dedup_on], keep="last").reset_index(drop=True)
    save_parquet(df, path)
    return df


def hash_id(*parts) -> str:
    """Stable 16-char id from any set of strings.

    Used as article_id so the same article fetched twice (historical run and
    live run) collapses to one row and gets scored by FinBERT only once.
    """
    joined = "||".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]