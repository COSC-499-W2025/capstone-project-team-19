from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlite3 import Connection

from src.api.dependencies import get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.api.schemas.project_ranking import ProjectRankingDTO, ProjectRankingItemDTO
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO, ResumeDetailDTO
from src.api.schemas.skills import SkillEventDTO, SkillsListDTO, SkillTimelineDTO
from src.db.users import get_user_by_username
from src.services.projects_service import list_projects, get_project_by_id
from src.services.project_ranking_service import get_project_ranking
from src.services.resumes_service import list_user_resumes, get_resume_by_id
from src.services.skills_service import get_user_skills, get_skill_timeline_data
from src.services.thumbnails_service import get_thumbnail

router = APIRouter(prefix="/public", tags=["public"])


def _resolve_user_id(conn: Connection, username: str) -> int:
    """Look up user_id by username; raise 404 if not found."""
    row = get_user_by_username(conn, username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row[0]  # (user_id, username, email)


@router.get("/{username}/projects", response_model=ApiResponse[ProjectListDTO])
def public_list_projects(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    rows = list_projects(conn, user_id)
    dto = ProjectListDTO(projects=[ProjectListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/projects/{project_id:int}", response_model=ApiResponse[ProjectDetailDTO])
def public_get_project(username: str, project_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    project = get_project_by_id(conn, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(success=True, data=ProjectDetailDTO(**project), error=None)


@router.get("/{username}/projects/{project_id:int}/thumbnail")
def public_get_thumbnail(username: str, project_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    result = get_thumbnail(conn, user_id, project_id)
    if result is None or result is False:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(result, media_type="image/png")


@router.get("/{username}/ranking", response_model=ApiResponse[ProjectRankingDTO])
def public_get_ranking(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    rows = get_project_ranking(conn, user_id)
    dto = ProjectRankingDTO(
        rankings=[
            ProjectRankingItemDTO(
                rank=i + 1,
                project_summary_id=r["project_summary_id"],
                project_name=r["project_name"],
                score=r["score"],
                manual_rank=r["manual_rank"],
            )
            for i, r in enumerate(rows)
        ]
    )
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/resumes", response_model=ApiResponse[ResumeListDTO])
def public_list_resumes(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    rows = list_user_resumes(conn, user_id)
    dto = ResumeListDTO(resumes=[ResumeListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/resumes/{resume_id:int}", response_model=ApiResponse[ResumeDetailDTO])
def public_get_resume(username: str, resume_id: int, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    resume = get_resume_by_id(conn, user_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ApiResponse(success=True, data=ResumeDetailDTO(**resume), error=None)


@router.get("/{username}/skills", response_model=ApiResponse[SkillsListDTO])
def public_get_skills(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    skills = get_user_skills(conn, user_id)
    dto = SkillsListDTO(skills=[SkillEventDTO(**s) for s in skills])
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{username}/skills/timeline", response_model=ApiResponse[SkillTimelineDTO])
def public_get_skills_timeline(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user_id(conn, username)
    data = get_skill_timeline_data(conn, user_id)
    return ApiResponse(success=True, data=SkillTimelineDTO(**data), error=None)
