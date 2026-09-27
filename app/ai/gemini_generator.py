from __future__ import annotations
import google.generativeai as genai
from app.config import settings

def generate(prompt: str, model_name: str | None = None) -> str:
    if not settings.google_api_key:
        raise RuntimeError("Gemini is not configured. Add GOOGLE_API_KEY to your .env file.")
    genai.configure(api_key=settings.google_api_key)
    try:
        response = genai.GenerativeModel(model_name or settings.gemini_workout_model).generate_content(prompt, request_options={"timeout": 45})
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response. Please try again.")
        return text.strip()
    except Exception as exc:
        raise RuntimeError(f"Gemini could not generate a response ({type(exc).__name__}). Check the model name and API access, then retry.") from exc
