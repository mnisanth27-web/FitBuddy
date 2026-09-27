# FitBuddy – AI Fitness Plan Generator using Gemini & Groq AI

FitBuddy is a beginner-friendly FastAPI and Jinja2 application that creates personalized seven-day fitness plans, gives a concise recovery tip, and revises a plan from user feedback. It stores the original and revised plan separately in SQLite.

## Features

- Gemini workout generation and Gemini Flash nutrition/recovery tips
- Groq workout generation and nutrition/recovery suggestions
- Select a provider on both generation and feedback forms
- Friendly errors for missing credentials and provider failures
- User validation and duplicate user ID handling
- Original plan preservation and feedback-based revisions
- Signed-cookie admin login, searchable/filterable dashboard, expandable plan comparison and user deletion
- JSON user endpoints and FastAPI Swagger/ReDoc documentation
- Responsive Jinja2 frontend with loading state

## Architecture

The browser submits forms to FastAPI routes. Routes validate inputs with Pydantic, call the centralized `app.ai.ai_service`, and store successful results through SQLAlchemy. Provider adapters live separately in `app/ai/`. SQLAlchemy creates the SQLite schema on application startup. Templates escape user and AI text by default; generated Markdown is shown as readable plain text.

## Technology

Python 3.10+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite, Jinja2, python-multipart, python-dotenv, Gemini API and Groq API.

## Project structure

```text
app/                 FastAPI app, routes, schemas, config, database and models
app/ai/              Gemini, Gemini Flash, Groq and orchestration services
templates/           Jinja2 pages
static/css/          Responsive styles
static/js/           Loading, filters and admin delete behavior
tests/               Automated tests with mocked AI calls
.env.example         Environment variable template
requirements.txt     Python dependencies
```

## Installation

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

On Linux/macOS, activate with `source venv/bin/activate` and copy `.env.example` to `.env` using `cp .env.example .env`.

## Configure AI providers

Edit `.env` and supply at least one provider key:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
GROQ_API_KEY=your_groq_api_key
GEMINI_WORKOUT_MODEL=gemini-1.5-pro
GEMINI_NUTRITION_MODEL=gemini-1.5-flash
GROQ_MODEL=openai/gpt-oss-120b
```

Model names can be changed to models available to your account. Missing keys and invalid/unavailable models produce a clear user-facing error. FitBuddy never fabricates generated plans or silently switches providers; select the other configured provider and retry.

## Admin and database setup

Set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and a random `SESSION_SECRET` in `.env`. The defaults are for local demonstration only. SQLite initializes automatically at startup using `DATABASE_URL=sqlite:///./fitbuddy.db`. Keep `.env` private; it is excluded by `.gitignore`.

The admin dashboard is at `/view-all-users`; sign in at `/admin/login`. This signed-cookie login is a basic college demo, not production authentication. Use HTTPS and replace it with a stronger identity and authorization system before public deployment.

## Run

From the project directory:

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API docs are at <http://127.0.0.1:8000/docs> and <http://127.0.0.1:8000/redoc>.

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Plan entry form |
| POST | `/generate-workout` | Generate and store a plan |
| POST | `/submit-feedback` | Generate and store a revision |
| GET/POST | `/admin/login` | Admin login |
| POST | `/admin/logout` | End admin session |
| GET | `/view-all-users` | Protected admin dashboard |
| GET | `/api/users` | List user profile summaries |
| GET | `/api/users/{user_id}` | User and plan data |
| DELETE | `/api/users/{user_id}` | Admin-only user and plan deletion |

## Tests

```bash
pytest
```

AI methods are mocked in the test suite, so tests never call Gemini or Groq.

## Troubleshooting

- **Provider not configured:** add its key to `.env` and restart Uvicorn.
- **Model unavailable:** change the corresponding model environment variable to one enabled for your API account.
- **Duplicate user ID:** choose another ID or retrieve your prior plan; the app does not overwrite a prior plan.
- **Admin login fails:** check `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env` and restart.
- **Database reset for a local demo:** stop the server and remove `fitbuddy.db`; the app creates a fresh database next startup.

## Fitness safety

FitBuddy provides general fitness and wellness information. It is not a substitute for advice from a qualified healthcare or fitness professional. If you have a medical condition, injury, or concern about exercise safety, consult an appropriate professional before starting a new exercise program. The AI prompt also discourages extreme dieting, unsafe rapid weight loss, dangerous exercise, and exercising through serious pain. For younger users or health concerns, seek appropriate professional guidance.

## Future enhancements

Potential extensions include account-based plan history, provider health checks, structured exercise libraries, progress tracking, and stronger production authentication.
