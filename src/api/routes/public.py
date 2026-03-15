from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlite3 import Connection

from src.api.dependencies import get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.public_schemas import (
    PublicProjectDetailDTO,
    PublicProjectListDTO,
    PublicProjectListItemDTO,
    PublicRankingDTO,
    PublicRankingItemDTO,
    PublicResumeDetailDTO,
    PublicSkillDTO,
    PublicSkillsListDTO,
)
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO
from src.api.schemas.skills import SkillTimelineDTO
from src.db.users import get_user_by_username
from src.services.public_portfolio_service import (
    get_public_project_detail,
    get_public_projects,
    get_public_ranking,
    get_public_resume_by_id,
    get_public_skills,
    is_portfolio_public,
)
from src.services.resumes_service import list_user_resumes
from src.services.skills_service import get_skill_timeline_data
from src.services.thumbnails_service import get_thumbnail

router = APIRouter(prefix="/public", tags=["public"])


def _resolve_user(conn: Connection, username: str) -> int:
    """Look up user_id by username; raise 404 if not found or portfolio not public."""
    row = get_user_by_username(conn, username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = row[0]
    if not is_portfolio_public(conn, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@router.get("/{username}/projects", response_model=ApiResponse[PublicProjectListDTO])
def public_list_projects(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    rows = get_public_projects(conn, user_id)
    dto = PublicProjectListDTO(projects=[PublicProjectListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/projects/{project_id:int}", response_model=ApiResponse[PublicProjectDetailDTO])
def public_get_project(username: str, project_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    project = get_public_project_detail(conn, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(success=True, data=PublicProjectDetailDTO(**project), error=None)


@router.get("/{username}/projects/{project_id:int}/thumbnail")
def public_get_thumbnail(username: str, project_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    # Only serve thumbnails for projects the user has made public
    row = conn.execute(
        "SELECT project_summary_id FROM project_summaries WHERE user_id = ? AND project_summary_id = ? AND is_public = 1",
        (user_id, project_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    result = get_thumbnail(conn, user_id, project_id)
    if result is None or result is False:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(result, media_type="image/png")


@router.get("/{username}/ranking", response_model=ApiResponse[PublicRankingDTO])
def public_get_ranking(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    rows = get_public_ranking(conn, user_id)
    dto = PublicRankingDTO(rankings=[PublicRankingItemDTO(**r) for r in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/resumes", response_model=ApiResponse[ResumeListDTO])
def public_list_resumes(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    rows = list_user_resumes(conn, user_id)
    dto = ResumeListDTO(resumes=[ResumeListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/resumes/{resume_id:int}", response_model=ApiResponse[PublicResumeDetailDTO])
def public_get_resume(username: str, resume_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    resume = get_public_resume_by_id(conn, user_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ApiResponse(success=True, data=PublicResumeDetailDTO(**resume), error=None)


@router.get("/{username}/skills", response_model=ApiResponse[PublicSkillsListDTO])
def public_get_skills(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    skills = get_public_skills(conn, user_id)
    dto = PublicSkillsListDTO(skills=[PublicSkillDTO(**s) for s in skills])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/skills/timeline", response_model=ApiResponse[SkillTimelineDTO])
def public_get_skills_timeline(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    data = get_skill_timeline_data(conn, user_id)
    return ApiResponse(success=True, data=SkillTimelineDTO(**data), error=None)
