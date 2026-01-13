from fastapi import APIRouter, Depends, Query
from sqlite3 import Connection

from src.api.dependencies import get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO
from src.services.projects_service import list_projects

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=ApiResponse[ProjectListDTO])
def get_projects(
    user_id: int = Query(..., description="User ID to fetch projects for"),
    conn: Connection = Depends(get_db),
):
    rows = list_projects(conn, user_id)

    dto = ProjectListDTO(
        projects=[ProjectListItemDTO(**row) for row in rows]
    )

    return ApiResponse(success=True, data=dto, error=None)
