"""Train the XGBoost model with purged walk-forward CV, run the
technicals-only vs technicals+sentiment ablation under BOTH the raw-return
and excess-return targets (same XGB config, same CV splits, same features
-- only the target changes), and save the final production model.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.features.build_features import ALL_FEATURE_COLS
from src.model.train import run_cv, train_final_model, TECHNICALS_ONLY_COLS
from src.utils.io import ensure_dirs, load_parquet

if __name__ == "__main__":
    ensure_dirs()

    df = load_parquet(config.PROCESSED / "features_trainable.parquet")
    print(f"loaded {len(df):,} trainable rows, {df['date'].nunique()} unique dates\n")

    print("=== ablation: technicals only (raw-return target) ===")
    tech_metrics, _ = run_cv(df, TECHNICALS_ONLY_COLS, label_col="label",
                               return_col="fwd_ret", label="technicals_only")

    print("\n=== full model: technicals + sentiment (raw-return target) ===")
    full_metrics, full_iter = run_cv(df, ALL_FEATURE_COLS, label_col="label",
                                        return_col="fwd_ret", label="technicals_plus_sentiment")

    print("\n=== ablation summary, raw-return target (mean across folds) ===")
    summary = pd.concat([tech_metrics, full_metrics]).groupby("model")[
        ["balanced_accuracy", "macro_f1", "baseline_balanced_accuracy", "return_spread"]
    ].mean()
    print(summary.to_string())

    delta_bal_acc = full_metrics["balanced_accuracy"].mean() - tech_metrics["balanced_accuracy"].mean()
    delta_spread = full_metrics["return_spread"].mean() - tech_metrics["return_spread"].mean()
    print(f"\nsentiment adds {delta_bal_acc*100:+.2f} points of balanced accuracy (raw target)")
    print(f"sentiment adds {delta_spread*100:+.3f}% to the up-minus-down return spread (raw target)")

    print("\n=== controlled comparison: raw return vs excess return target ===")
    print("(same XGBoost config, same CV splits, same full feature set -- only the target changes)\n")

    raw_full_metrics, _ = run_cv(df, ALL_FEATURE_COLS, label_col="label",
                                   return_col="fwd_ret", label="raw_target")
    excess_full_metrics, _ = run_cv(df, ALL_FEATURE_COLS, label_col="label_excess",
                                      return_col="fwd_ret_excess", label="excess_target")

    target_summary = pd.concat([raw_full_metrics, excess_full_metrics]).groupby("model")[
        ["balanced_accuracy", "macro_f1", "return_spread"]
    ].mean()
    print(target_summary.to_string())

    print("\n=== does sentiment help under the excess-return target? ===")
    tech_excess_metrics, _ = run_cv(df, TECHNICALS_ONLY_COLS, label_col="label_excess",
                                      return_col="fwd_ret_excess", label="technicals_only_excess")
    full_excess_metrics, full_iter_excess = run_cv(
        df, ALL_FEATURE_COLS, label_col="label_excess",
        return_col="fwd_ret_excess", label="technicals_plus_sentiment_excess"
    )

    excess_ablation = pd.concat([tech_excess_metrics, full_excess_metrics]).groupby("model")[
        ["balanced_accuracy", "macro_f1", "return_spread"]
    ].mean()
    print(excess_ablation.to_string())

    excess_delta = (full_excess_metrics["balanced_accuracy"].mean()
                     - tech_excess_metrics["balanced_accuracy"].mean())
    print(f"\nunder excess-return target, sentiment adds {excess_delta*100:+.2f} points of balanced accuracy")
    print(f"(compare to {delta_bal_acc*100:+.2f} points under the raw-return target)")

    print(f"\ntraining final production model on all data "
          f"(excess target, n_estimators={full_iter_excess})...")
    final_model = train_final_model(df, ALL_FEATURE_COLS, n_estimators=full_iter_excess,
                                       label_col="label_excess")
    final_model.save_model(str(config.MODEL_PATH))
    print(f"saved -> {config.MODEL_PATH.relative_to(config.ROOT)}")

    report = {
        "ablation_summary_raw": summary.to_dict(),
        "target_comparison": target_summary.to_dict(),
        "ablation_summary_excess": excess_ablation.to_dict(),
        "sentiment_delta_balanced_accuracy_raw": delta_bal_acc,
        "sentiment_delta_balanced_accuracy_excess": excess_delta,
        "n_trainable_rows": len(df),
        "n_estimators_final": full_iter_excess,
        "final_model_label_col": "label_excess",
        "feature_cols": ALL_FEATURE_COLS,
    }
    with open(config.METRICS_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"saved -> {config.METRICS_PATH.relative_to(config.ROOT)}")