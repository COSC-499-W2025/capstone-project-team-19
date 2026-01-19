from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO, ResumeDetailDTO
from src.services.resumes_service import list_user_resumes, get_resume_by_id

router = APIRouter(prefix="/resume", tags=["resume"])

@router.get("", response_model=ApiResponse[ResumeListDTO])
def get_resumes(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_user_resumes(conn, user_id)
    dto = ResumeListDTO(resumes=[ResumeListItemDTO(**row) for row in rows])
    
    return ApiResponse(success=True, data=dto, error=None)

@router.get("/{resume_id}", response_model=ApiResponse[ResumeDetailDTO])
def get_resume(
    resume_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    resume = get_resume_by_id(conn, user_id, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    dto = ResumeDetailDTO(**resume)
    return ApiResponse(success=True, data=dto, error=None)
