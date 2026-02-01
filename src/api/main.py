from fastapi import FastAPI
from src.api.routes.projects import router as projects_router
from src.api.routes.skills import router as skills_router
from src.api.routes.resumes import router as resumes_router
from src.api.routes.github import router as github_router


from src.api.routes.consent import router as consent_router
from src.api.routes.portfolio import router as portfolio_router
from src.api.auth.routes import router as auth_router

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
app.include_router(portfolio_router)
