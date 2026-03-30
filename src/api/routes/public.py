import shutil
import tempfile

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlite3 import Connection
from typing import Optional

from src.api.dependencies import get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.activity_heatmap import ActivityHeatmapDataDTO
from src.api.schemas.skills import ActivityByDateMatrixDTO
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
from src.db.resumes import get_resume_snapshot
from src.db.skill_preferences import has_skill_preferences
from src.db.users import get_user_by_username
from src.services.skill_preferences_service import get_highlighted_skills_for_display
from src.export.resume_docx import export_resume_record_to_docx
from src.export.resume_pdf import export_resume_record_to_pdf
from src.services.public_portfolio_service import (
    get_portfolio_settings,
    get_public_project_detail,
    get_public_projects,
    get_public_ranking,
    get_public_resume_by_id,
    get_public_skills,
    is_portfolio_public,
)
from src.services.activity_heatmap_service import get_activity_heatmap_data
from src.services.resumes_service import list_user_resumes
from src.services.skills_service import get_skill_timeline_data, get_activity_by_date_grid
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


@router.get("/{username}/status")
def public_portfolio_status(username: str, conn: Connection = Depends(get_db)):
    """Returns whether a user exists and whether their portfolio is public."""
    row = get_user_by_username(conn, username)
    if not row:
        return {"exists": False, "is_public": False}
    user_id = row[0]
    return {"exists": True, "is_public": bool(is_portfolio_public(conn, user_id))}


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


@router.get("/{username}/skills/activity-by-date", response_model=ApiResponse[ActivityByDateMatrixDTO])
def public_get_activity_by_date(
    username: str,
    year: Optional[int] = Query(None),
    conn: Connection = Depends(get_db),
):
    user_id = _resolve_user(conn, username)
    public_ids = {
        row[0]
        for row in conn.execute(
            "SELECT project_summary_id FROM project_summaries WHERE user_id = ? AND is_public = 1",
            (user_id,),
        ).fetchall()
    }
    data = get_activity_by_date_grid(conn, user_id, year=year, project_ids=public_ids)
    return ApiResponse(success=True, data=ActivityByDateMatrixDTO(**data), error=None)


@router.get("/{username}/projects/{project_id:int}/activity-heatmap/data", response_model=ApiResponse[ActivityHeatmapDataDTO])
def public_get_activity_heatmap_data(
    username: str,
    project_id: int,
    conn: Connection = Depends(get_db),
):
    user_id = _resolve_user(conn, username)
    row = conn.execute(
        "SELECT project_summary_id FROM project_summaries WHERE user_id = ? AND project_summary_id = ? AND is_public = 1",
        (user_id, project_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        data = get_activity_heatmap_data(conn, user_id, project_id)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Project not found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")
    return ApiResponse(success=True, data=ActivityHeatmapDataDTO(**data), error=None)


@router.get("/{username}/resumes/{resume_id:int}/export/docx", response_class=FileResponse)
def public_export_resume_docx(
    username: str,
    resume_id: int,
    background_tasks: BackgroundTasks,
    conn: Connection = Depends(get_db),
):
    """Export a public resume to DOCX format (no auth required)."""
    user_id = _resolve_user(conn, username)
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")

    highlighted_skills = None
    if has_skill_preferences(conn, user_id, "resume", context_id=resume_id) or \
       has_skill_preferences(conn, user_id, "global"):
        highlighted_skills = get_highlighted_skills_for_display(
            conn, user_id, context="resume", context_id=resume_id
        )

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(shutil.rmtree, temp_dir, True)

    filepath = export_resume_record_to_docx(username=username, record=record, out_dir=temp_dir, highlighted_skills=highlighted_skills)
    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{username}/resumes/{resume_id:int}/export/pdf", response_class=FileResponse)
def public_export_resume_pdf(
    username: str,
    resume_id: int,
    background_tasks: BackgroundTasks,
    conn: Connection = Depends(get_db),
):
    """Export a public resume to PDF format (no auth required)."""
    user_id = _resolve_user(conn, username)
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")

    highlighted_skills = None
    if has_skill_preferences(conn, user_id, "resume", context_id=resume_id) or \
       has_skill_preferences(conn, user_id, "global"):
        highlighted_skills = get_highlighted_skills_for_display(
            conn, user_id, context="resume", context_id=resume_id
        )

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(shutil.rmtree, temp_dir, True)

    filepath = export_resume_record_to_pdf(username=username, record=record, out_dir=temp_dir, highlighted_skills=highlighted_skills)
    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/pdf",
    )


@router.get("/{username}/active-resume", response_model=ApiResponse[Optional[PublicResumeDetailDTO]])
def public_get_active_resume(username: str, conn: Connection = Depends(get_db)):
    user_id = _resolve_user(conn, username)
    settings = get_portfolio_settings(conn, user_id)
    active_resume_id = settings.get("active_resume_id")
    if not active_resume_id:
        return ApiResponse(success=True, data=None, error=None)
    resume = get_public_resume_by_id(conn, user_id, active_resume_id)
    if not resume:
        return ApiResponse(success=True, data=None, error=None)
    return ApiResponse(success=True, data=PublicResumeDetailDTO(**resume), error=None)
