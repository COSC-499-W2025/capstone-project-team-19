from fastapi import FastAPI
from src.api.routes import (
    projects_router,
    projects_ranking_router,
    feedback_router,
    project_dates_router,
    skills_router,
    resumes_router,
    portfolio_router,
    github_router,
    consent_router,
    portfolio_router,
    export_router,
)
from src.api.auth.routes import router as auth_router


app = FastAPI(title="Capstone API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(projects_ranking_router)
app.include_router(projects_router)
app.include_router(feedback_router)
app.include_router(project_dates_router)
app.include_router(skills_router)
app.include_router(resumes_router)
app.include_router(consent_router)
app.include_router(github_router)
app.include_router(portfolio_router)
app.include_router(export_router)
