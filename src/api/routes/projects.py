from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO
from src.api.schemas.uploads import UploadDTO, ClassificationsRequest, ProjectTypesRequest
from src.services.projects_service import list_projects
from src.services.uploads_service import start_upload, get_upload_status, submit_classifications, submit_project_types


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
    payload: ProjectTypesRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = submit_project_types(conn, user_id, upload_id, payload.project_types)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)
