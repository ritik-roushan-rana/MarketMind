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


def _fix_booster_base_score(booster):
    """SHAP >=0.46 tries to float() the XGBoost multiclass base_score, but
    XGBoost 2.x stores it as '[5E-1,5E-1,5E-1]' (one value per class).
    SHAP chokes on the brackets.  Fix: load the booster config JSON, rewrite
    base_score to a plain scalar, and save it back before SHAP reads it.
    This is the only reliable fix that works across all SHAP versions.
    """
    import json, re
    cfg = json.loads(booster.save_config())

    def _fix_node(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "base_score" and isinstance(v, str) and v.startswith("["):
                    # '[5E-1,5E-1,5E-1]' -> take first value -> 0.5
                    nums = re.findall(r"[0-9Ee.+\-]+", v)
                    node[k] = str(float(nums[0])) if nums else "0.5"
                else:
                    _fix_node(v)
        elif isinstance(node, list):
            for item in node:
                _fix_node(item)

    _fix_node(cfg)
    booster.load_config(json.dumps(cfg))
    return booster


def build_explainer(model):
    """Build a TreeExplainer, working around the SHAP >=0.46 bug where it
    cannot parse the multiclass base_score array '[5E-1,5E-1,5E-1]' stored
    by XGBoost 2.x.  We fix the booster config in-place before SHAP reads it.
    """
    booster = _fix_booster_base_score(model.get_booster())
    return shap.TreeExplainer(booster)


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