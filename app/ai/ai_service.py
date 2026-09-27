from __future__ import annotations
from app.ai import gemini_generator, gemini_flash_generator, groq_generator
from app.models import User

SAFETY = "Use safe, moderate, general wellness guidance. Avoid extreme dieting, unsafe rapid weight loss, dangerous exercise, or exercising through serious pain. Recommend professional guidance for minors, injuries, or health concerns. Return readable Markdown with seven clearly labeled days and warm-up, exercises with sets/reps/rest, cooldown and recovery guidance."

def _profile(user: User) -> str:
    return (f"Name: {user.name}; age: {user.age}; weight: {user.weight} kg; goal: {user.goal}; "
            f"intensity: {user.intensity}; experience: {user.experience_level}.")

def _generate(provider: str, prompt: str) -> str:
    if provider == "Gemini":
        return gemini_generator.generate(prompt)
    if provider == "Groq":
        return groq_generator.generate(prompt)
    raise ValueError("Choose Gemini or Groq as the AI provider.")

def generate_workout(user: User, provider: str) -> str:
    prompt = f"Create a personalized seven-day fitness plan. {SAFETY}\n{_profile(user)}\nFor every day provide focus, warm-up, exercises, sets, reps or duration, rest, cooldown and recovery. Adjust safely to the goal and experience."
    return _generate(provider, prompt)

def generate_nutrition_tip(user: User, provider: str) -> str:
    prompt = f"Give one concise practical nutrition or recovery tip for goal {user.goal}. {SAFETY} State no medical claims and keep it under 80 words."
    if provider == "Gemini":
        return gemini_flash_generator.generate_tip(prompt)
    return groq_generator.generate(prompt)

def update_workout_plan(user: User, original: str, feedback: str, provider: str) -> str:
    prompt = f"Update the complete seven-day plan in response to user feedback. Preserve safety and the selected goal and intensity. Incorporate the feedback where appropriate, and explain an unsafe or unsuitable request gently. Return all seven days in readable Markdown, with warm-up, exercises/sets/reps/rest, cooldown and recovery.\nProfile: {_profile(user)}\nOriginal plan:\n{original}\nUser feedback:\n{feedback}"
    return _generate(provider, prompt)
