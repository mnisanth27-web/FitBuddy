from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.ai_service import generate_workout, generate_nutrition_tip, update_workout_plan
from app.database import get_db
from app.models import User, WorkoutPlan
from app.formatting import render_markdown
from app.schemas import UserInput, FeedbackRequest, GOALS

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.filters["markdown"] = render_markdown
DISCLAIMER = "FitBuddy provides general fitness and wellness information. It is not a substitute for advice from a qualified healthcare or fitness professional. If you have a medical condition, injury, or concern about exercise safety, consult an appropriate professional before starting a new exercise program."

def render_error(request: Request, message: str, status: int = 400):
    return templates.TemplateResponse(request=request, name="index.html", context={"goals": GOALS, "error": message}, status_code=status)

def latest_plan(user: User):
    return max(user.plans, key=lambda p: p.created_at or datetime.min, default=None)

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"goals": GOALS})

@router.post("/generate-workout", response_class=HTMLResponse, summary="Generate a personalized seven-day workout plan")
def generate_workout_route(request: Request, name: str = Form(...), user_id: str = Form(...), age: int = Form(...), weight: float = Form(...), goal: str = Form(...), intensity: str = Form(...), experience_level: str = Form("Beginner"), provider: str = Form("Gemini"), db: Session = Depends(get_db)):
    try:
        payload = UserInput(name=name, user_id=user_id, age=age, weight=weight, goal=goal, intensity=intensity, experience_level=experience_level, provider=provider)
    except ValidationError as exc:
        return render_error(request, "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()))
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if user and user.plans:
        return render_error(request, "That User ID already has a plan. Choose a new User ID to generate another plan.", 409)
    if user is None:
        user = User(user_id=payload.user_id, name=payload.name, age=payload.age, weight=payload.weight, goal=payload.goal, intensity=payload.intensity, experience_level=payload.experience_level)
        db.add(user)
    else:
        for key in ("name", "age", "weight", "goal", "intensity", "experience_level"):
            setattr(user, key, getattr(payload, key))
    try:
        db.flush()
        plan_text = generate_workout(user, payload.provider)
        tip = generate_nutrition_tip(user, payload.provider)
        plan = WorkoutPlan(user=user, original_plan=plan_text, nutrition_tip=tip, ai_provider=payload.provider)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return templates.TemplateResponse(request=request, name="result.html", context={"user": user, "plan": plan, "provider": payload.provider, "disclaimer": DISCLAIMER, "success": None})
    except RuntimeError as exc:
        db.rollback()
        return render_error(request, str(exc), 503)
    except Exception:
        db.rollback()
        return render_error(request, "Unable to save or generate your plan right now. Please try again.", 500)

@router.post("/submit-feedback", response_class=HTMLResponse, summary="Revise the original plan using user feedback")
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...), provider: str = Form(...), db: Session = Depends(get_db)):
    try:
        payload = FeedbackRequest(user_id=user_id, feedback=feedback, provider=provider)
    except ValidationError as exc:
        return render_error(request, "; ".join(e["msg"] for e in exc.errors()))
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if not user:
        return render_error(request, "We could not find that User ID. Please check it and try again.", 404)
    plan = latest_plan(user)
    if not plan:
        return render_error(request, "This user does not have an original workout plan yet.", 404)
    try:
        revised = update_workout_plan(user, plan.original_plan, payload.feedback.strip(), payload.provider)
        plan.updated_plan = revised
        plan.feedback = payload.feedback.strip()
        plan.updated_at = datetime.now(timezone.utc)
        plan.ai_provider = payload.provider
        db.commit()
        db.refresh(plan)
        return templates.TemplateResponse(request=request, name="result.html", context={"user": user, "plan": plan, "provider": payload.provider, "disclaimer": DISCLAIMER, "success": "Your workout plan has been updated successfully."})
    except RuntimeError as exc:
        db.rollback()
        return render_error(request, str(exc), 503)
    except Exception:
        db.rollback()
        return render_error(request, "Unable to update your plan right now. Please try again.", 500)

def require_admin(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=401, detail="Admin login required")

@router.get("/admin/login", response_class=HTMLResponse, include_in_schema=False)
def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@router.post("/admin/login", include_in_schema=False)
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    from app.config import settings
    import secrets
    if secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(password, settings.admin_password):
        request.session["is_admin"] = True
        return RedirectResponse("/view-all-users", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": "Invalid admin username or password."}, status_code=401)

@router.post("/admin/logout", include_in_schema=False)
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)

@router.get("/view-all-users", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("is_admin"):
        return RedirectResponse("/admin/login", status_code=303)
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    records = [{"user": u, "plan": latest_plan(u)} for u in users]
    return templates.TemplateResponse(request=request, name="all_users.html", context={"records": records})

@router.get("/api/users", summary="List users and their latest plan metadata")
def api_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [{"user_id": u.user_id, "name": u.name, "age": u.age, "weight": u.weight, "goal": u.goal, "intensity": u.intensity, "created_at": u.created_at, "plan_count": len(u.plans)} for u in users]

@router.get("/api/users/{user_id}", summary="Get a user's profile and workout plans")
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.user_id, "name": user.name, "age": user.age, "weight": user.weight, "goal": user.goal, "intensity": user.intensity, "plans": [{"original_plan": p.original_plan, "updated_plan": p.updated_plan, "feedback": p.feedback, "nutrition_tip": p.nutrition_tip, "ai_provider": p.ai_provider} for p in user.plans]}

@router.delete("/api/users/{user_id}", summary="Delete a user and associated plans")
def delete_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User and associated plans deleted."}
