import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from src.api.routes.projects import router as projects_router
from src.api.routes.skills import router as skills_router
from src.api.routes.resumes import router as resumes_router
from src.api.routes.github import router as github_router


from src.api.routes.consent import router as consent_router
from src.api.auth.routes import router as auth_router

# Load environment variables from a local .env (if present).
# Important for local development (JWT_SECRET, OAuth config).
# Skip under pytest to avoid cross-test side effects from a developer's local .env.
if "pytest" not in sys.modules:
    # Only override if the variable is missing/empty in the current process environment.
    # This avoids surprising overrides, but fixes the common case where JWT_SECRET exists as an empty string in the shell/environment.
    override = os.getenv("JWT_SECRET") in (None, "")
    load_dotenv(override=override)

app = FastAPI(title="Capstone API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(skills_router)
app.include_router(resumes_router)
app.include_router(consent_router)
app.include_router(github_router)
