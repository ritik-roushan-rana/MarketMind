"""FastAPI app entrypoint. Run with:
    uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, predict, tickers

app = FastAPI(title="Market Sentiment Dashboard API")

# Loosened for hackathon demo convenience -- tighten allow_origins to your
# actual frontend URL before deploying this anywhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(tickers.router, tags=["tickers"])
app.include_router(predict.router, tags=["predict"])