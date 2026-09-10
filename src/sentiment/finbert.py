"""FinBERT sentiment scoring with a persistent cache.

Scores each article exactly once. Rerunning this script after you've added
new news articles only scores the new ones -- everything already in
sentiment_cache.parquet is skipped, keyed by article_id.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# torch and transformers are imported lazily inside _load_model(). Importing
# torch alone costs a few hundred MB of RSS, and on a 1GB container that is
# memory the API cannot spare for a request it can serve entirely from the
# precomputed sentiment cache.

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.utils.io import load_parquet, save_parquet

_MODEL = None
_TOKENIZER = None
_DEVICE = None


def _get_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_model():
    """Loads once per process. First call downloads ~400MB from
    huggingface.co -- expect a pause the very first time you run this."""
    global _MODEL, _TOKENIZER, _DEVICE
    if _MODEL is not None:
        return _TOKENIZER, _MODEL, _DEVICE

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    _DEVICE = _get_device()
    print(f"  loading {config.FINBERT_MODEL} on {_DEVICE} ...")

    if _DEVICE == "cpu":
        # One intra-op thread. Each extra thread carries its own workspace,
        # which is wasted memory on a 1-2 core container.
        torch.set_num_threads(config.TORCH_NUM_THREADS)

    _TOKENIZER = AutoTokenizer.from_pretrained(config.FINBERT_MODEL)
    _MODEL = AutoModelForSequenceClassification.from_pretrained(
        config.FINBERT_MODEL,
        # Materialise weights straight into their final tensors. The default
        # builds a randomly-initialised model first and then loads the
        # checkpoint over it, so peak memory is ~2x the model.
        low_cpu_mem_usage=True,
    )
    _MODEL.to(_DEVICE)
    _MODEL.eval()
    print(f"  labels: {_MODEL.config.id2label}")
    return _TOKENIZER, _MODEL, _DEVICE


def _build_text(headline: str, summary: str) -> str:
    """Headline plus first sentence of the summary only. Full article bodies
    dilute the signal and blow past the token limit."""
    headline = (headline or "").strip()
    summary = (summary or "").strip()
    if summary:
        first_sentence = summary.split(". ")[0][:200]
        return f"{headline}. {first_sentence}"
    return headline


def score_texts(texts: list) -> pd.DataFrame:
    """Batch-score a list of strings. Returns one row per input text with
    positive/negative/neutral probabilities, in the SAME order as the input.
    """
    if not texts:
        return pd.DataFrame(columns=["sent_positive", "sent_negative", "sent_neutral"])

    import torch

    tokenizer, model, device = _load_model()
    id2label = {i: lbl.lower() for i, lbl in model.config.id2label.items()}

    # sort by length so padding within a batch is minimal, then restore order
    order = np.argsort([len(t) for t in texts])
    texts_sorted = [texts[i] for i in order]

    all_probs = np.zeros((len(texts), len(id2label)), dtype=np.float32)

    bs = config.FINBERT_BATCH_SIZE
    for start in tqdm(range(0, len(texts_sorted), bs), desc="  scoring", unit="batch"):
        batch = texts_sorted[start:start + bs]
        enc = tokenizer(
            batch, padding=True, truncation=True,
            max_length=config.FINBERT_MAX_LENGTH, return_tensors="pt",
        ).to(device)

        with torch.inference_mode():
            logits = model(**enc).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()

        batch_idx = order[start:start + bs]
        all_probs[batch_idx] = probs

        # Release the batch's activations before allocating the next one.
        del enc, logits

    cols = [id2label[i] for i in range(len(id2label))]
    out = pd.DataFrame(all_probs, columns=cols)
    return out.rename(columns={
        "positive": "sent_positive",
        "negative": "sent_negative",
        "neutral": "sent_neutral",
    })[["sent_positive", "sent_negative", "sent_neutral"]]


def load_cache() -> pd.DataFrame:
    if config.SENTIMENT_CACHE_PATH.exists():
        return load_parquet(config.SENTIMENT_CACHE_PATH)
    return pd.DataFrame(columns=config.SENTIMENT_SCHEMA)


def update_cache(news_df: pd.DataFrame) -> pd.DataFrame:
    """Score whatever in news_df isn't already in the cache, append, save.
    Safe to call repeatedly -- rerunning after collecting more news only
    costs you the new articles."""
    cache = load_cache()
    already = set(cache["article_id"]) if not cache.empty else set()

    todo = news_df[~news_df["article_id"].isin(already)].copy()
    todo = todo.drop_duplicates(subset=["article_id"])

    if todo.empty:
        print("  nothing new to score, cache already covers all articles")
        return cache

    # Newest first, then cap. A cold cache can hold hundreds of unscored
    # articles, and scoring them all in one request is what OOM-killed the
    # API container. The dashboard only surfaces the newest handful, and the
    # remainder get picked up by later calls as the cache warms.
    limit = config.FINBERT_MAX_ARTICLES_PER_REQUEST
    if "published_utc" in todo.columns:
        todo = todo.sort_values("published_utc", ascending=False)
    skipped = max(0, len(todo) - limit)
    if skipped:
        print(f"  capping this run at {limit:,} newest articles "
              f"({skipped:,} deferred to a later call)")
        todo = todo.head(limit)

    print(f"  scoring {len(todo):,} new articles "
          f"({len(already):,} already cached)")

    texts = [
        _build_text(h, s) for h, s in zip(todo["headline"], todo["summary"])
    ]
    scores = score_texts(texts)
    scores["article_id"] = todo["article_id"].values

    scores["sentiment_score"] = scores["sent_positive"] - scores["sent_negative"]
    scores["confidence"] = 1 - scores["sent_neutral"]
    scores = scores[config.SENTIMENT_SCHEMA]

    merged = pd.concat([cache, scores], ignore_index=True)
    merged = merged.drop_duplicates(subset=["article_id"], keep="last")
    save_parquet(merged, config.SENTIMENT_CACHE_PATH)

    print(f"  cache now has {len(merged):,} scored articles")
    return merged


def join_sentiment(news_df: pd.DataFrame, cache_df: pd.DataFrame = None) -> pd.DataFrame:
    """Attach sentiment columns onto a news table by article_id. Used by the
    feature builder, both for the historical table and for a live pull."""
    cache_df = cache_df if cache_df is not None else load_cache()
    return news_df.merge(cache_df, on="article_id", how="left")


def audit(scored: pd.DataFrame, news_df: pd.DataFrame) -> pd.DataFrame:
    """How much of the news table actually has a sentiment score, per ticker.
    A ticker with a low coverage % has articles that failed to score --
    usually an empty headline that slipped past the length filter."""
    j = join_sentiment(news_df, scored)
    g = j.groupby("ticker")
    out = pd.DataFrame({
        "articles": g.size(),
        "scored": g["sentiment_score"].apply(lambda s: s.notna().sum()),
        "mean_sentiment": g["sentiment_score"].mean().round(3),
        "mean_confidence": g["confidence"].mean().round(3),
    })
    out["coverage_pct"] = (100 * out["scored"] / out["articles"]).round(1)
    return out.sort_values("articles")