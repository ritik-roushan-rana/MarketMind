"""Simple liveness/readiness check -- confirms the model actually loaded
before the frontend starts hammering /predict."""
from fastapi import APIRouter, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from api.dependencies import get_model, get_feature_order
from api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(model=Depends(get_model), feature_cols=Depends(get_feature_order)):
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        n_features=len(feature_cols),
        tickers_available=len(config.TICKERS),
    )