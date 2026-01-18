from fastapi import APIRouter, Depends
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO
from src.services.resumes_service import list_user_resumes

router = APIRouter(prefix="/resume", tags=["resume"])

@router.get("", response_model=ApiResponse[ResumeListDTO])
def get_resumes(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_user_resumes(conn, user_id)
    dto = ResumeListDTO(resumes=[ResumeListItemDTO(**row) for row in rows])
    
    return ApiResponse(success=True, data=dto, error=None)