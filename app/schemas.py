from typing import Literal
from pydantic import BaseModel, Field, field_validator

GOALS = ["Weight Loss", "Muscle Gain", "General Wellness", "Flexibility", "Strength", "General Fitness"]
class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=0, le=500)
    goal: str
    intensity: Literal["Low", "Medium", "High"]
    experience_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    provider: Literal["Gemini", "Groq"] = "Gemini"
    @field_validator("name", "user_id")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value
    @field_validator("goal")
    @classmethod
    def valid_goal(cls, value: str) -> str:
        if value not in GOALS:
            raise ValueError("Choose a listed fitness goal")
        return value

class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    feedback: str = Field(min_length=3, max_length=1000)
    provider: Literal["Gemini", "Groq"] = "Gemini"
