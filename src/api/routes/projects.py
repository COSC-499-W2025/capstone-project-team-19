from fastapi import APIRouter, Depends, Query, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.services.projects_service import list_projects, get_project_by_id

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=ApiResponse[ProjectListDTO])
def get_projects(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_projects(conn, user_id)
    dto = ProjectListDTO(projects=[ProjectListItemDTO(**row) for row in rows])
    
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