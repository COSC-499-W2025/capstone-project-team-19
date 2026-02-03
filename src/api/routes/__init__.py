"""
src/api/routes/__init__.py

Convenience exports for FastAPI routers.
This keeps `src/api/main.py` imports clean and centralized.
"""

from src.api.routes.projects import router as projects_router
from src.api.routes.projects_ranking import router as projects_ranking_router
from src.api.routes.project_dates import router as project_dates_router
from src.api.routes.skills import router as skills_router
from src.api.routes.resumes import router as resumes_router
from src.api.routes.github import router as github_router
from src.api.routes.consent import router as consent_router

__all__ = [
    "projects_router",
    "projects_ranking_router",
    "project_dates_router",
    "skills_router",
    "resumes_router",
    "github_router",
    "consent_router",
]