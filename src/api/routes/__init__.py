"""
src/api/routes/__init__.py

Convenience exports for FastAPI routers.
This keeps `src/api/main.py` imports clean and centralized.
"""

from src.api.routes.projects import router as projects_router
from src.api.routes.projects_ranking import router as projects_ranking_router
from src.api.routes.feedback import router as feedback_router
from src.api.routes.project_dates import router as project_dates_router
from src.api.routes.skills import router as skills_router
from src.api.routes.resumes import router as resumes_router
from src.api.routes.portfolio import router as portfolio_router
from src.api.routes.github import router as github_router
from src.api.routes.google_drive import router as google_drive_router
from src.api.routes.consent import router as consent_router
from src.api.routes.portfolio import router as portfolio_router
from src.api.routes.export import router as export_router
from src.api.routes.thumbnails import router as thumbnails_router

__all__ = [
    "projects_router",
    "projects_ranking_router",
    "feedback_router",
    "project_dates_router",
    "skills_router",
    "resumes_router",
    "portfolio_router",
    "github_router",
    "google_drive_router",
    "consent_router",
    "portfolio_router",
    "export_router",
    "thumbnails_router",
]
