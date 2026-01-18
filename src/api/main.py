from fastapi import FastAPI
from src.api.routes.projects import router as projects_router
from src.api.routes.skills import router as skills_router
from src.api.routes.resumes import router as resumes_router


app = FastAPI(title="Capstone API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(projects_router)
app.include_router(skills_router)
app.include_router(resumes_router)