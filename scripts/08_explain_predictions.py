"""Compute SHAP explanations for the trained model: global feature
importance (sanity check -- does sentiment actually show up as
meaningful?) plus a worked example for the most recent prediction.
"""
import sys
from pathlib import Path

from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.features.build_features import ALL_FEATURE_COLS
from src.features.sentiment_features import SENTIMENT_FEATURE_COLS
from src.model.explain import build_explainer, explain_row, global_importance, format_for_llm
from src.utils.io import ensure_dirs, load_parquet

if __name__ == "__main__":
    ensure_dirs()

    df = load_parquet(config.PROCESSED / "features_trainable.parquet")

    model = XGBClassifier()
    model.load_model(str(config.MODEL_PATH))

    explainer = build_explainer(model)

    print("=== global feature importance (mean |SHAP|, all classes) ===")
    importance = global_importance(explainer, df, ALL_FEATURE_COLS)
    print(importance.head(15).to_string())

    sentiment_ranks = importance[importance["feature"].isin(SENTIMENT_FEATURE_COLS)]
    ranks = [importance.index[importance.feature == f].tolist()[0] + 1
             for f in sentiment_ranks["feature"]]
    print(f"\nsentiment features occupy ranks {sorted(ranks)} out of {len(ALL_FEATURE_COLS)}")
    print(sentiment_ranks.to_string())

    print("\n=== worked example: most recent row ===")
    last_row = df.sort_values("date").iloc[-1]
    X_last = last_row[ALL_FEATURE_COLS].values.astype(float).reshape(1, -1)
    proba = model.predict_proba(X_last)[0]
    pred_class = int(proba.argmax())

    contrib = explain_row(explainer, last_row, ALL_FEATURE_COLS, pred_class)
    prompt_text = format_for_llm(
        last_row["ticker"], last_row["date"].date(), pred_class, proba[pred_class], contrib
    )
    print(prompt_text)