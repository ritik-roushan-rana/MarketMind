"""The main endpoint: live sentiment + price data -> feature build ->
prediction -> SHAP -> plain-English explanation, for one ticker."""
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_explainer, get_feature_order, get_model
from api.schemas import PredictionResponse
from api.services.live_predict import PredictionError, predict_ticker

router = APIRouter()


@router.get("/predict/{ticker}", response_model=PredictionResponse)
def predict(
    ticker: str,
    model=Depends(get_model),
    feature_cols=Depends(get_feature_order),
    explainer=Depends(get_explainer),
):
    ticker = ticker.upper()
    try:
        result = predict_ticker(ticker, model, feature_cols, explainer)
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"prediction failed: {exc}")
    return PredictionResponse(**result)