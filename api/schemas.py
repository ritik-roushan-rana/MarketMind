"""Pydantic request/response models -- the API's public contract with the
frontend. Kept separate from route logic so the shape of the API is
readable in one place."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TickerListResponse(BaseModel):
    tickers: List[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    n_features: int
    tickers_available: int


class Driver(BaseModel):
    feature: str
    value: float
    shap: float


class PredictionResponse(BaseModel):
    ticker: str
    as_of_date: str
    predicted_label: str              # "up" | "flat" | "down"
    predicted_proba: float            # probability of the predicted class
    class_probabilities: Dict[str, float]
    top_drivers: List[Driver]
    explanation: str
    headlines_used: List[str] = Field(default_factory=list)
    warning: Optional[str] = None     # e.g. "used cached snapshot, live fetch failed"