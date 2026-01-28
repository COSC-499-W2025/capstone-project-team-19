from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.api.schemas.uploads import (
    UploadDTO,
    ClassificationsRequest,
    ProjectTypesRequest,
    DedupResolveRequestDTO,
    UploadProjectFilesDTO,
    MainFileRequestDTO,
)
from src.services.projects_service import list_projects, get_project_by_id
from src.services.uploads_service import (
    start_upload,
    get_upload_status,
    resolve_dedup,
    submit_classifications,
    submit_project_types,
    list_project_files,
    set_project_main_file,
)
from src.api.schemas.project_ranking import (
    ProjectRankingDTO,
    ProjectRankingItemDTO,
    ReplaceProjectRankingRequestDTO,
    PatchProjectRankingRequestDTO,
)
from src.services.project_ranking_service import (
    get_project_ranking,
    replace_project_ranking,
    set_project_manual_rank,
    reset_project_ranking,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ApiResponse[ProjectListDTO])
def get_projects(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_projects(conn, user_id)
    dto = ProjectListDTO(projects=[ProjectListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.post("/upload", response_model=ApiResponse[UploadDTO])
def post_projects_upload(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = start_upload(conn, user_id, file)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get("/upload/{upload_id}", response_model=ApiResponse[UploadDTO])
def get_projects_upload(
    upload_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/dedup/resolve", response_model=ApiResponse[UploadDTO])
def post_upload_dedup_resolve(
    upload_id: int,
    body: DedupResolveRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = resolve_dedup(conn, user_id, upload_id, body.decisions)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/classifications", response_model=ApiResponse[UploadDTO])
def post_upload_classifications(
    upload_id: int,
    payload: ClassificationsRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = submit_classifications(conn, user_id, upload_id, payload.assignments)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/project-types", response_model=ApiResponse[UploadDTO])
def post_upload_project_types(
    upload_id: int,
    body: ProjectTypesRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = submit_project_types(conn, user_id, upload_id, body.project_types)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project_name}/files",
    response_model=ApiResponse[UploadProjectFilesDTO],
)
def get_upload_project_files(
    upload_id: int,
    project_name: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = list_project_files(conn, user_id, upload_id, project_name)
    return ApiResponse(success=True, data=UploadProjectFilesDTO(**data), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_name}/main-file",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_main_file(
    upload_id: int,
    project_name: str,
    body: MainFileRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = set_project_main_file(conn, user_id, upload_id, project_name, body.relpath)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get("/ranking", response_model=ApiResponse[ProjectRankingDTO])
def get_projects_ranking(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
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
def put_projects_ranking(
    body: ReplaceProjectRankingRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
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
def patch_project_ranking(
    project_id: int,
    body: PatchProjectRankingRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
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
def post_projects_ranking_reset(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
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


@router.get("/{project_id}", response_model=ApiResponse[ProjectDetailDTO])
def get_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    project = get_project_by_id(conn, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    dto = ProjectDetailDTO(**project)
    return ApiResponse(success=True, data=dto, error=None)
