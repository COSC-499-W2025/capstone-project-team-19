from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlite3 import Connection

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.thumbnails import ThumbnailUploadDTO
from src.services.thumbnails_service import (
    get_thumbnail,
    remove_thumbnail,
    upload_thumbnail,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/{project_id:int}/thumbnail",
    response_model=ApiResponse[ThumbnailUploadDTO],
)
def post_thumbnail(
    project_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        result = upload_thumbnail(conn, user_id, project_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ApiResponse(
        success=True,
        data=ThumbnailUploadDTO(**result),
        error=None,
    )


@router.get("/{project_id:int}/thumbnail")
def get_project_thumbnail(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    result = get_thumbnail(conn, user_id, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(result, media_type="image/png")


@router.delete(
    "/{project_id:int}/thumbnail",
    response_model=ApiResponse[None],
)
def delete_thumbnail(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    result = remove_thumbnail(conn, user_id, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return ApiResponse(success=True, data=None, error=None)
