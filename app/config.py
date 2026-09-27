from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db")
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    gemini_workout_model = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-1.5-pro")
    gemini_nutrition_model = os.getenv("GEMINI_NUTRITION_MODEL", "gemini-1.5-flash")
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "change_this_password")
    session_secret = os.getenv("SESSION_SECRET", "local-demo-change-me")

settings = Settings()
