"""Score every collected article with FinBERT, caching results by article_id.

First run downloads the model (~400MB) and scores everything you've
collected so far -- expect a few minutes on CPU, faster on Apple Silicon
via MPS. Every run after that only scores newly added articles.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.sentiment import finbert
from src.utils.io import ensure_dirs, load_parquet

if __name__ == "__main__":
    ensure_dirs()

    news_path = config.NEWS_DIR / "news_history.parquet"
    if not news_path.exists():
        sys.exit(f"no news found at {news_path} -- run 02_collect_news.py first")

    news = load_parquet(news_path)
    print(f"loaded {len(news):,} articles from news_history.parquet\n")

    cache = finbert.update_cache(news)

    print("\naudit:")
    print(finbert.audit(cache, news).to_string())