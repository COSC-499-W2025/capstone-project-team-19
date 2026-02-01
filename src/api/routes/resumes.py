from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO, ResumeDetailDTO, ResumeGenerateRequestDTO, ResumeEditRequestDTO
from src.services.resumes_service import list_user_resumes, get_resume_by_id, generate_resume, edit_resume

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


@router.post("/generate", response_model=ApiResponse[ResumeDetailDTO], status_code=201)
def post_resume_generate(
    request: ResumeGenerateRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    resume = generate_resume(
        conn,
        user_id,
        name=request.name,
        project_ids=request.project_ids,
    )

    if not resume:
        raise HTTPException(status_code=400, detail="No valid projects found for the given IDs")

    dto = ResumeDetailDTO(**resume)
    return ApiResponse(success=True, data=dto, error=None)


@router.post("/{resume_id}/edit", response_model=ApiResponse[ResumeDetailDTO])
def post_resume_edit(
    resume_id: int,
    request: ResumeEditRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    resume = edit_resume(
        conn,
        user_id,
        resume_id,
        project_name=request.project_name,
        scope=request.scope,
        name=request.name,
        display_name=request.display_name,
        summary_text=request.summary_text,
        contribution_bullets=request.contribution_bullets,
        contribution_edit_mode=request.contribution_edit_mode,
        key_role=request.key_role,
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume or project not found")

    dto = ResumeDetailDTO(**resume)
    return ApiResponse(success=True, data=dto, error=None)
