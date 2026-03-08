from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from src.api.routes import (
    projects_router,
    projects_ranking_router,
    feedback_router,
    project_dates_router,
    skills_router,
    resumes_router,
    portfolio_router,
    github_router,
    google_drive_router,
    consent_router,
    export_router,
    thumbnails_router,
    activity_heatmap_router,
)
from src.api.auth.routes import router as auth_router

from fastapi.middleware.cors import CORSMiddleware

_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

app = FastAPI(title="Capstone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    origin = request.headers.get("origin")
    if origin in _ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


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
app.include_router(google_drive_router)
app.include_router(portfolio_router)
app.include_router(export_router)
app.include_router(thumbnails_router)
app.include_router(activity_heatmap_router)
