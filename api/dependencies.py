"""Loads the trained model, feature order, and SHAP explainer ONCE when the
API process starts, not on every request.
"""
import json
import sys
import traceback
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
try:
    _explainer = build_explainer(_model)
except Exception as exc:  # explanations are optional -- the API still serves
    traceback.print_exc()
    print(f"[startup] WARNING: explainer unavailable ({exc.__class__.__name__}); "
          f"predictions will be served without SHAP drivers")
    _explainer = None

print(f"[startup] ready -- {len(_feature_order)} features, "
      f"{len(config.TICKERS)} tickers available")


def get_model() -> XGBClassifier:
    return _model


def get_feature_order() -> list:
    return _feature_order


def get_explainer():
    return _explainer
