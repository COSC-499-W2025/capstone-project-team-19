from fastapi import APIRouter, Depends, Query
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.skills import SkillEventDTO, SkillsListDTO, SkillTimelineDTO, ProjectSkillMatrixDTO, ActivityByDateMatrixDTO
from src.services.skills_service import get_user_skills, get_skill_timeline_data, get_project_skill_matrix_data, get_activity_by_date_grid

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("", response_model=ApiResponse[SkillsListDTO])
def get_skills(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    skills = get_user_skills(conn, user_id)
    dto = SkillsListDTO(skills=[SkillEventDTO(**s) for s in skills])
    return ApiResponse(success=True, data=dto, error=None)

@router.get("/timeline", response_model=ApiResponse[SkillTimelineDTO])
def get_skills_timeline(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = get_skill_timeline_data(conn, user_id)
    dto = SkillTimelineDTO(**data)

    return ApiResponse(success=True, data=dto, error=None)


@router.get("/project-matrix", response_model=ApiResponse[ProjectSkillMatrixDTO])
def get_project_skill_matrix(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = get_project_skill_matrix_data(conn, user_id)
    dto = ProjectSkillMatrixDTO(**data)
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/activity-by-date", response_model=ApiResponse[ActivityByDateMatrixDTO])
def get_activity_by_date(
    year: int | None = Query(None, description="Filter to a specific year; if omitted, shows all data"),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = get_activity_by_date_grid(conn, user_id, year=year)
    dto = ActivityByDateMatrixDTO(**data)
    return ApiResponse(success=True, data=dto, error=None)