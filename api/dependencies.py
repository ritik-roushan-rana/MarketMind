"""Loads the trained model, feature order, and SHAP explainer ONCE when the
API process starts, not on every request.
"""
import json
import sys
from pathlib import Path

from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from src.model.explain import build_explainer

print("[startup] loading model...")
_model = XGBClassifier()
_model.load_model(str(config.MODEL_PATH))

print("[startup] loading feature order...")
with open(config.FEATURE_ORDER_PATH) as f:
    _feature_order = json.load(f)

print("[startup] building SHAP explainer...")
_explainer = build_explainer(_model)

print(f"[startup] ready -- {len(_feature_order)} features, "
      f"{len(config.TICKERS)} tickers available")


def get_model() -> XGBClassifier:
    return _model


def get_feature_order() -> list:
    return _feature_order


def get_explainer():
    return _explainer
