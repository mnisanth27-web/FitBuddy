from app.ai.gemini_generator import generate
from app.config import settings

def generate_tip(prompt: str) -> str:
    return generate(prompt, settings.gemini_nutrition_model)
