"""Lists the tickers the model actually supports -- lets the frontend
build a dropdown without hardcoding the list on the client side."""
from fastapi import APIRouter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config
from api.schemas import TickerListResponse

router = APIRouter()


@router.get("/tickers", response_model=TickerListResponse)
def list_tickers():
    return TickerListResponse(tickers=config.TICKERS)