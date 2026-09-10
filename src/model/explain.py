"""SHAP-based explanations for individual predictions.

Turns "the model predicts UP" into "the model predicts UP mainly because
of X, Y, Z" -- grounding the LLM explainer in actual feature attributions
instead of letting it free-associate about why a stock might move.

Attributions come from XGBoost's built-in TreeSHAP (``pred_contribs=True``)
rather than the ``shap`` package, so the runtime has no dependency on shap's
model parser -- see _NativeTreeExplainer for why that matters.  The shape
handling below still tolerates the list-per-class layout in case an explainer
that returns it is ever swapped back in.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config

LABEL_NAMES = {0: "flat", 1: "up", 2: "down"}


class _NativeTreeExplainer:
    """Drop-in replacement for shap.TreeExplainer backed by XGBoost's own
    TreeSHAP implementation (``pred_contribs=True``).

    Same algorithm, same numbers -- but it reads the booster directly instead
    of round-tripping it through shap's XGBTreeModelLoader, which cannot parse
    the per-class ``base_score`` vector ('[5E-1,5E-1,5E-1]') that XGBoost >=2.0
    regenerates in memory for multi:softprob models.  Patching base_score on
    disk or via load_config() does not help: shap re-serializes the live
    booster with save_raw(), and the vector comes straight back.
    """

    def __init__(self, booster):
        self._booster = booster

    def shap_values(self, X):
        """Returns (n_rows, n_features, n_classes) for multiclass, or
        (n_rows, n_features) for binary/regression -- matching the shapes
        _class_shap() and global_importance() already handle."""
        X = np.asarray(X, dtype=float)
        contribs = self._booster.predict(xgboost.DMatrix(X), pred_contribs=True)

        if contribs.ndim == 3:
            # (n_rows, n_classes, n_features + 1) -> drop bias, move classes last
            return np.transpose(contribs[:, :, :-1], (0, 2, 1))
        return contribs[:, :-1]  # (n_rows, n_features + 1) -> drop bias


def build_explainer(model):
    """Build a TreeSHAP explainer for a trained XGBoost model."""
    booster = model.get_booster() if hasattr(model, "get_booster") else model
    return _NativeTreeExplainer(booster)


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
    """Top_k features driving THIS prediction for THIS row."""
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
    """Mean absolute SHAP value per feature across all classes and rows."""
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
    """Structured, factual prompt fragment for the LLM explainer."""
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
