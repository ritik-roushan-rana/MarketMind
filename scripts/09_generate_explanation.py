"""End-to-end: load the model, pick the most recent prediction, run SHAP,
and generate a plain-English explanation via Gemini.

This is the last box in the offline half of the architecture -- everything
past this point is the live FastAPI path, which reuses these same
functions on fresh data instead of historical data.
"""
import sys
from pathlib import Path

from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.features.build_features import ALL_FEATURE_COLS
from src.model.explain import build_explainer, explain_row, format_for_llm
from src.model.llm_explainer import explain
from src.utils.io import ensure_dirs, load_parquet

if __name__ == "__main__":
    ensure_dirs()

    df = load_parquet(config.PROCESSED / "features_trainable.parquet")

    model = XGBClassifier()
    model.load_model(str(config.MODEL_PATH))
    explainer = build_explainer(model)

    last_row = df.sort_values("date").iloc[-1]
    X_last = last_row[ALL_FEATURE_COLS].values.astype(float).reshape(1, -1)
    proba = model.predict_proba(X_last)[0]
    pred_class = int(proba.argmax())

    contrib = explain_row(explainer, last_row, ALL_FEATURE_COLS, pred_class)
    prompt_text = format_for_llm(
        last_row["ticker"], last_row["date"].date(), pred_class, proba[pred_class], contrib
    )

    print("=== SHAP summary sent to the LLM ===")
    print(prompt_text)

    print("\n=== plain-English explanation ===")
    print(explain(prompt_text))