"""XGBoost training with purged walk-forward CV, plus the
technicals-only vs technicals+sentiment ablation that is the actual
scientific claim of this project: does sentiment add predictive power
over price features alone?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from src.features.technical import TECHNICAL_FEATURE_COLS
from src.model.splits import purged_walk_forward_splits

MARKET_COLS = ["spy_ret_1d", "vix_level", "vix_change_1d", "day_of_week"]
TECHNICALS_ONLY_COLS = TECHNICAL_FEATURE_COLS + MARKET_COLS


def _fit_predict(train_df, val_df, feature_cols, label_col="label"):
    X_train = train_df[feature_cols].values
    y_train = train_df[label_col].astype(int).values
    X_val = val_df[feature_cols].values
    y_val = val_df[label_col].astype(int).values

    model = XGBClassifier(**config.XGB_PARAMS)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    preds = model.predict(X_val)
    return model, preds, y_val


def run_cv(
    df: pd.DataFrame,
    feature_cols: list,
    label_col: str = "label",
    return_col: str = "fwd_ret",
    label: str = "model",
):
    """Runs purged walk-forward CV. Returns (metrics_df, avg_best_iteration).

    label_col / return_col let the exact same harness evaluate either the
    raw-return label+fwd_ret or the excess-return label+fwd_ret_excess,
    with everything else -- XGB params, CV splits, feature set -- held
    fixed. That's what makes the raw-vs-excess comparison controlled.

    avg_best_iteration is the mean early-stopping point across folds --
    used to pick a sane, non-overfit tree count for the final production
    model, which has no held-out validation set of its own.
    """
    df = df.dropna(subset=[label_col])
    dates = df["date"].unique()
    results, best_iters = [], []

    for i, (train_dates, val_dates) in enumerate(
        purged_walk_forward_splits(dates, config.CV_N_SPLITS, config.CV_EMBARGO_DAYS), 1
    ):
        train_df = df[df["date"].isin(train_dates)]
        val_df = df[df["date"].isin(val_dates)]
        if train_df.empty or val_df.empty:
            continue

        model, preds, y_val = _fit_predict(train_df, val_df, feature_cols, label_col)

        bal_acc = balanced_accuracy_score(y_val, preds)
        macro_f1 = f1_score(y_val, preds, average="macro")
        ret_up = val_df.loc[preds == 1, return_col].mean()
        ret_down = val_df.loc[preds == 2, return_col].mean()
        ret_up = 0.0 if np.isnan(ret_up) else ret_up
        ret_down = 0.0 if np.isnan(ret_down) else ret_down
        majority_class = pd.Series(y_val).mode()[0]
        baseline_bal_acc = balanced_accuracy_score(y_val, np.full_like(y_val, majority_class))
        best_iter = getattr(model, "best_iteration", None)

        m = dict(
            fold=i, model=label,
            balanced_accuracy=bal_acc, macro_f1=macro_f1,
            baseline_balanced_accuracy=baseline_bal_acc,
            return_spread=ret_up - ret_down,
            n_train=len(train_df), n_val=len(val_df),
        )
        results.append(m)
        if best_iter:
            best_iters.append(best_iter)

        print(f"  [{label}] fold {i}: bal_acc={bal_acc:.3f} "
              f"(baseline {baseline_bal_acc:.3f})  macro_f1={macro_f1:.3f}  "
              f"spread={m['return_spread']:+.4f}  "
              f"n_train={m['n_train']}  n_val={m['n_val']}")

    avg_best_iter = int(np.mean(best_iters)) + 1 if best_iters else 300
    return pd.DataFrame(results), avg_best_iter


def train_final_model(df: pd.DataFrame, feature_cols: list, n_estimators: int,
                       label_col: str = "label"):
    """Train on ALL available data -- the artifact that ships with the
    dashboard. CV above is for honest evaluation only; this model has no
    held-out set left, so n_estimators is fixed from the CV folds' average
    early-stopping point rather than left to overfit on 2000 rounds."""
    df = df.dropna(subset=[label_col])
    X = df[feature_cols].values
    y = df[label_col].astype(int).values

    params = {k: v for k, v in config.XGB_PARAMS.items() if k != "early_stopping_rounds"}
    params["n_estimators"] = n_estimators
    model = XGBClassifier(**params)
    model.fit(X, y, verbose=False)
    return model