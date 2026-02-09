from fastapi import APIRouter, Depends, Query, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.google_drive import (
    DriveStartRequest, DriveStartResponse,
    DriveFilesResponse, DriveFileDTO, DriveLinkRequest
)
from src.services.google_drive_service import (
    drive_start_connection, drive_handle_callback,
    drive_list_files, drive_link_files
)
from src.services.uploads_service import get_upload_status

router = APIRouter(tags=["google_drive"])


@router.get("/auth/google/callback")
def get_google_callback(code: str = Query(...), state: str = Query(None), conn: Connection = Depends(get_db)):
    """OAuth callback endpoint for Google Drive."""
    try:
        result = drive_handle_callback(conn, code, state)
        return {"success": True, "message": "Google Drive connected successfully", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete Google authorization: {str(e)}")


@router.post("/projects/upload/{upload_id}/projects/{project}/drive/start", response_model=ApiResponse[DriveStartResponse])
def post_drive_start(upload_id: int, project: str, body: DriveStartRequest, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """Start Google Drive connection flow for a project."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    result = drive_start_connection(conn, user_id, upload_id, project, body.connect_now)
    return ApiResponse(success=True, data=DriveStartResponse(auth_url=result.get("auth_url")), error=None)


@router.get("/projects/upload/{upload_id}/projects/{project}/drive/files", response_model=ApiResponse[DriveFilesResponse])
def get_drive_files(upload_id: int, project: str, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """List user's Google Drive files for linking."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    files = drive_list_files(conn, user_id)
    if files is None:
        raise HTTPException(status_code=401, detail="Google Drive not connected. Please connect Google Drive first.")
    file_dtos = [DriveFileDTO(id=f["id"], name=f["name"], mime_type=f["mimeType"]) for f in files]
    return ApiResponse(success=True, data=DriveFilesResponse(files=file_dtos), error=None)


@router.post("/projects/upload/{upload_id}/projects/{project}/drive/link", response_model=ApiResponse[dict])
def post_drive_link(upload_id: int, project: str, body: DriveLinkRequest, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """Link Google Drive files to a project's local files."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    links = [link.model_dump() for link in body.links]
    result = drive_link_files(conn, user_id, project, links)
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to link files. Check that Google Drive is connected.")
    return ApiResponse(success=True, data=result, error=None)
