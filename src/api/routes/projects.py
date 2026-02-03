from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse, DeleteResultDTO
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.api.schemas.uploads import (
    UploadDTO,
    ClassificationsRequest,
    ProjectTypesRequest,
    DedupResolveRequestDTO,
    UploadProjectFilesDTO,
    MainFileRequestDTO,
)
from src.services.projects_service import (
    list_projects,
    get_project_by_id,
    delete_project,
    delete_all_projects,
)
from src.services.uploads_service import (
    start_upload,
    get_upload_status,
    resolve_dedup,
    submit_classifications,
    submit_project_types,
    list_project_files,
    set_project_main_file,
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

@router.get(
    "/upload/{upload_id}/projects/{project_name}/text/sections",
    response_model=ApiResponse[MainFileSectionsDTO]
)
def get_main_file_sections(
    upload_id: int,
    project_name: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = list_main_file_sections(conn, user_id, upload_id, project_name)
    if not data:
        raise HTTPException(status_code=404, detail="Main file sections not found")
    return ApiResponse(success=True, data=MainFileSectionsDTO(**data), error=None)

@router.post(
    "/upload/{upload_id}/projects/{project_name}/text/contributions",
    response_model=ApiResponse[MainFileContributionDTO]
)
def post_main_file_contributed_sections(
    upload_id: int,
    project_name: str,
    body: ContributedSectionsRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = set_main_file_contributed_sections(conn, user_id, upload_id, project_name, body.relpath)
    return ApiResponse(success=True, data=MainFileContributionDTO(**data), error=None)


@router.delete("", response_model=ApiResponse[DeleteResultDTO])
def delete_all_user_projects(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete all projects for the current user."""
    count = delete_all_projects(conn, user_id)
    return ApiResponse(success=True, data=DeleteResultDTO(deleted_count=count), error=None)


# Use `:int` so non-integers like "ranking" never match this route.
@router.get("/{project_id:int}", response_model=ApiResponse[ProjectDetailDTO])
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


@router.delete("/{project_id:int}", response_model=ApiResponse[None])
def delete_single_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete a single project by ID."""
    deleted = delete_project(conn, user_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(success=True, data=None, error=None)
