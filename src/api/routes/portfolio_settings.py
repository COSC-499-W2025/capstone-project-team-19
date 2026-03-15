from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlite3 import Connection
from typing import Optional

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.services.public_portfolio_service import (
    get_portfolio_settings,
    upsert_portfolio_settings,
    set_project_visibility,
)

router = APIRouter(prefix="/portfolio-settings", tags=["portfolio-settings"])


class PortfolioSettingsUpdateDTO(BaseModel):
    portfolio_public: Optional[bool] = None
    active_resume_id: Optional[int] = None
    clear_active_resume: Optional[bool] = False


class ProjectVisibilityUpdateDTO(BaseModel):
    is_public: bool


@router.get("", response_model=ApiResponse[dict])
def get_settings(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    settings = get_portfolio_settings(conn, user_id)
    return ApiResponse(success=True, data=settings, error=None)


@router.put("", response_model=ApiResponse[dict])
def update_settings(
    payload: PortfolioSettingsUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    settings = upsert_portfolio_settings(
        conn,
        user_id,
        portfolio_public=payload.portfolio_public,
        active_resume_id=payload.active_resume_id,
        clear_active_resume=payload.clear_active_resume or False,
    )
    return ApiResponse(success=True, data=settings, error=None)


@router.patch("/projects/{project_summary_id}/visibility", response_model=ApiResponse[dict])
def update_project_visibility(
    project_summary_id: int,
    payload: ProjectVisibilityUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    updated = set_project_visibility(conn, user_id, project_summary_id, payload.is_public)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(
        success=True,
        data={"project_summary_id": project_summary_id, "is_public": payload.is_public},
        error=None,
    )
