from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.project_ranking import (
    ProjectRankingDTO,
    ProjectRankingItemDTO,
    ReplaceProjectRankingRequestDTO,
    PatchProjectRankingRequestDTO,
)
from src.services.projects_service import list_projects
from src.services.project_ranking_service import (
    get_project_ranking,
    replace_project_ranking,
    set_project_manual_rank,
    reset_project_ranking,
)


# Keep these endpoints clearly project-scoped by using the /projects prefix.
router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/ranking", response_model=ApiResponse[ProjectRankingDTO])
def get_projects_ranking(user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
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

@router.put("/ranking", response_model=ApiResponse[ProjectRankingDTO])
def put_projects_ranking(body: ReplaceProjectRankingRequestDTO, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    if len(body.project_ids) != len(set(body.project_ids)):
        raise HTTPException(status_code=400, detail="Duplicate project_ids are not allowed.")

    # "replace entire ranking order" means caller must provide all projects for this user
    existing_ids = {p["project_summary_id"] for p in list_projects(conn, user_id)}
    provided_ids = set(body.project_ids)
    if provided_ids != existing_ids:
        raise HTTPException(
            status_code=400,
            detail="project_ids must include every project_summary_id for this user (no extras, no missing).",
        )

    try:
        replace_project_ranking(conn, user_id, body.project_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

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

@router.patch("/{project_id}/ranking", response_model=ApiResponse[ProjectRankingDTO])
def patch_project_ranking(project_id: int, body: PatchProjectRankingRequestDTO, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    if body.rank is not None and body.rank < 1:
        raise HTTPException(status_code=400, detail="rank must be >= 1 (or null to clear manual ranking).")

    project_count = len(list_projects(conn, user_id))
    if body.rank is not None and body.rank > project_count:
        raise HTTPException(status_code=400, detail=f"rank must be <= {project_count}.")

    try:
        set_project_manual_rank(conn, user_id, project_id, body.rank)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

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

@router.post("/ranking/reset", response_model=ApiResponse[ProjectRankingDTO])
def post_projects_ranking_reset(user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    reset_project_ranking(conn, user_id)
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
