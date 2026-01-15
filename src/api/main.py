from fastapi import FastAPI
from src.api.routes.projects import router as projects_router

app = FastAPI(title="Capstone API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(projects_router)
