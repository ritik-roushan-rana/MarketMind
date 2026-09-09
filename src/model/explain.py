"""SHAP-based explanations for individual predictions.

Turns "the model predicts UP" into "the model predicts UP mainly because
of X, Y, Z" -- grounding the LLM explainer in actual feature attributions
instead of letting it free-associate about why a stock might move.

Handles the shape shap.TreeExplainer actually returns for a multiclass
XGBClassifier, which has changed across shap versions:
  - some versions: a list of (n_rows, n_features) arrays, one per class
  - current versions (tested on shap 0.52): a single
    (n_rows, n_features, n_classes) array
Both are handled so this doesn't silently break on a shap version bump.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config

LABEL_NAMES = {0: "flat", 1: "up", 2: "down"}


def build_explainer(model):
    """TreeExplainer works directly on the underlying XGBoost booster --
    fast, exact (not a sampling approximation), no background dataset
    needed for tree models.

    Pass the raw booster via get_booster() rather than the sklearn wrapper.
    Some SHAP versions fail to parse the multiclass base_score stored as
    '[5E-1,5E-1,5E-1]' from the wrapper's metadata -- the booster object
    bypasses that code path entirely.
    """
    try:
        return shap.TreeExplainer(model.get_booster())
    except Exception:
        return shap.TreeExplainer(model)


def _class_shap(shap_values, predicted_class: int, row_idx: int = 0):
    """Normalizes whichever shape this shap version returned down to a
    single (n_features,) array for one row's predicted class."""
    if isinstance(shap_values, list):
        return shap_values[predicted_class][row_idx]
    if shap_values.ndim == 3:
        return shap_values[row_idx, :, predicted_class]
    return shap_values[row_idx]


def explain_row(explainer, row: pd.Series, feature_cols: list,
                 predicted_class: int, top_k: int = None) -> pd.DataFrame:
    """Top_k features driving THIS prediction for THIS row, for the class
    the model actually predicted -- not "how important is this feature in
    general" but "why did the model say UP for NVDA today"."""
    top_k = top_k or config.SHAP_TOP_K
    X = row[feature_cols].values.astype(float).reshape(1, -1)

    shap_values = explainer.shap_values(X)
    class_shap = _class_shap(shap_values, predicted_class)

    contrib = pd.DataFrame({
        "feature": feature_cols,
        "value": X[0],
        "shap": class_shap,
    })
    contrib["abs_shap"] = contrib["shap"].abs()
    contrib = contrib.sort_values("abs_shap", ascending=False).head(top_k)
    return contrib[["feature", "value", "shap"]].reset_index(drop=True)


def global_importance(explainer, df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Mean absolute SHAP value per feature, averaged across all classes
    and all rows -- "which features matter most overall", for a sanity
    check / importance chart, not for any single prediction."""
    X = df[feature_cols].values.astype(float)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        stacked = np.stack([np.abs(sv) for sv in shap_values], axis=0)
        mean_abs = stacked.mean(axis=(0, 1))
    elif shap_values.ndim == 3:
        mean_abs = np.abs(shap_values).mean(axis=(0, 2))
    else:
        mean_abs = np.abs(shap_values).mean(axis=0)

    out = pd.DataFrame({"feature": feature_cols, "mean_abs_shap": mean_abs})
    return out.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def format_for_llm(ticker: str, date, predicted_class: int, predicted_proba: float,
                    contrib: pd.DataFrame, headlines: list = None) -> str:
    """Structured, factual prompt fragment for the LLM explainer -- numbers
    only, no narrative, so the LLM explains what actually happened instead
    of inventing a story it wasn't given."""
    label = LABEL_NAMES.get(predicted_class, str(predicted_class))
    lines = [
        f"Ticker: {ticker}   Date: {date}   Prediction: {label.upper()} (p={predicted_proba:.2f})",
        "Top drivers (SHAP):",
    ]
    for _, r in contrib.iterrows():
        lines.append(f"  {r['feature']:<22} = {r['value']:+.4f}  -> shap {r['shap']:+.4f}")
    if headlines:
        lines.append("Headlines:")
        for h in headlines[:3]:
            lines.append(f"  - {h}")
    return "\n".join(lines)