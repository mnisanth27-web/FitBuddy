import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app import routes
from app.database import Base, get_db
from app.ai import ai_service

@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(ai_service, "generate_workout", lambda user, provider: "DAY 1\nEasy full body\nWarm-up: 5 min\nSquats: 2 x 8; rest 60 sec\nCooldown: walking")
    monkeypatch.setattr(ai_service, "generate_nutrition_tip", lambda user, provider: "Drink water and include a balanced meal.")
    monkeypatch.setattr(ai_service, "update_workout_plan", lambda user, original, feedback, provider: original + "\nUpdated with: " + feedback)
    monkeypatch.setattr(routes, "generate_workout", lambda user, provider: "DAY 1\nEasy full body\nWarm-up: 5 min\nSquats: 2 x 8; rest 60 sec\nCooldown: walking")
    monkeypatch.setattr(routes, "generate_nutrition_tip", lambda user, provider: "Drink water and include a balanced meal.")
    monkeypatch.setattr(routes, "update_workout_plan", lambda user, original, feedback, provider: original + "\nUpdated with: " + feedback)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()

def form(user_id="demo_1"):
    return {"name":"Demo User","user_id":user_id,"age":"25","weight":"68","goal":"General Fitness","intensity":"Medium","experience_level":"Beginner","provider":"Gemini"}

def test_home_and_database_creation(client):
    assert client.get("/").status_code == 200
    assert "FitBuddy" in client.get("/").text

def test_input_validation(client):
    data = form(); data["age"] = "10"
    response = client.post("/generate-workout", data=data)
    assert response.status_code == 400
    assert "age" in response.text

def test_user_creation_and_plan_generation(client):
    response = client.post("/generate-workout", data=form())
    assert response.status_code == 200
    assert "DAY 1" in response.text
    assert client.get("/api/users/demo_1").json()["plans"][0]["original_plan"].startswith("DAY 1")

def test_duplicate_user_id(client):
    client.post("/generate-workout", data=form())
    response = client.post("/generate-workout", data=form())
    assert response.status_code == 409

def test_feedback_keeps_original(client):
    client.post("/generate-workout", data=form())
    response = client.post("/submit-feedback", data={"user_id":"demo_1","feedback":"Add more cardio","provider":"Groq"})
    assert response.status_code == 200
    data = client.get("/api/users/demo_1").json()["plans"][0]
    assert data["original_plan"].startswith("DAY 1")
    assert "Add more cardio" in data["updated_plan"]

def test_admin_auth_and_user_deletion(client):
    client.post("/generate-workout", data=form())
    assert client.get("/view-all-users", follow_redirects=False).status_code == 303
    login = client.post("/admin/login", data={"username":"admin","password":"change_this_password"}, follow_redirects=False)
    assert login.status_code == 303
    assert client.get("/view-all-users").status_code == 200
    deleted = client.delete("/api/users/demo_1")
    assert deleted.status_code == 200
    assert client.get("/api/users/demo_1").status_code == 404


def test_groq_gpt_oss_disables_reasoning_output(monkeypatch):
    from types import SimpleNamespace
    from app.config import settings
    from app.ai import groq_generator
    captured = {}
    class FakeGroq:
        def __init__(self, **kwargs):
            pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured.update(kwargs)
                    message = SimpleNamespace(content="A useful fitness plan")
                    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])
    monkeypatch.setattr(groq_generator, "Groq", FakeGroq)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "groq_model", "openai/gpt-oss-120b")
    assert groq_generator.generate("Write a safe plan") == "A useful fitness plan"
    assert captured["include_reasoning"] is False
    assert captured["reasoning_effort"] == "low"

def test_plan_markdown_is_formatted_and_sanitized():
    from app.formatting import render_markdown
    rendered = str(render_markdown("**Strong**\n\n| Day | Workout |\n| --- | --- |\n| 1 | Squats |\n\n<script>alert(1)</script>"))
    assert "<strong>Strong</strong>" in rendered
    assert "<table>" in rendered
    assert "<script>" not in rendered