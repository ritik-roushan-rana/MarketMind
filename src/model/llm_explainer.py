"""Turns the structured, factual SHAP summary into a plain-English
explanation via the Gemini API.

The prompt is deliberately numbers-only (see explain.format_for_llm) --
the model is told exactly what to explain and instructed not to invent
anything beyond it. This is what keeps the explainer "explainable AI"
rather than a chatbot bolted onto a predictor: the narrative is grounded
in the same SHAP values a human analyst would look at.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore", message="there are non-text parts")

import sys
from pathlib import Path

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config

SYSTEM_PROMPT = (
    "You are explaining a stock direction prediction from a machine learning "
    "model to a retail-facing dashboard user. You will be given the model's "
    "prediction, its confidence, and the top features (with SHAP values) "
    "that drove that specific prediction, plus optionally a few recent "
    "headlines.\n\n"
    "Rules:\n"
    "- Use ONLY the numbers and headlines given to you. Never invent a "
    "fact, statistic, or news event not present in the input.\n"
    "- Write 2-3 short sentences, plain English, no jargon like 'SHAP' or "
    "'feature importance' in the output -- translate them into what they "
    "actually mean (e.g. 'an unusual spike in news coverage' instead of "
    "'news_count_zscore').\n"
    "- Do not give investment advice or tell the reader what to do.\n"
    "- Be honest about low confidence -- if p is close to 0.33-0.4, say the "
    "signal is weak, don't oversell it.\n"
    "- This is not financial advice and must not be phrased as a "
    "recommendation to buy or sell."
)


def _client() -> genai.Client:
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get a free key at "
            "aistudio.google.com/apikey and put it in your .env file."
        )
    return genai.Client(api_key=config.GEMINI_API_KEY)


def explain(prompt_text: str) -> str:
    """prompt_text is the output of src.model.explain.format_for_llm()."""
    client = _client()
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=config.LLM_MAX_TOKENS,
        ),
    )
    return response.text