from groq import Groq
from app.config import settings

def generate(prompt: str) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("Groq is not configured. Add GROQ_API_KEY to your .env file.")
    try:
        model = settings.groq_model
        options = {}
        if model.startswith("openai/gpt-oss-"):
            options = {"reasoning_effort": "low", "include_reasoning": False}
        result = Groq(api_key=settings.groq_api_key, timeout=45.0).chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_completion_tokens=8192,
            **options,
        )
        if not result.choices:
            raise RuntimeError("Groq returned no completion choices. Please try again.")
        choice = result.choices[0]
        text = choice.message.content
        if isinstance(text, str) and text.strip():
            return text.strip()
        finish_reason = choice.finish_reason or "unknown"
        if finish_reason == "length":
            raise RuntimeError("Groq reached its response limit before producing answer text. Please try again.")
        raise RuntimeError(f"Groq returned no answer text (finish reason: {finish_reason}). Please retry or choose another provider.")
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"Groq could not generate a response ({type(exc).__name__}). Check the model name and API access, then retry.") from exc
