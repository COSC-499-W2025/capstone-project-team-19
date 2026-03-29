from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse, DeleteResultDTO
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO, ResumeDetailDTO, ResumeGenerateRequestDTO, ResumeEditRequestDTO, AddProjectRequestDTO
from src.api.helpers import resolve_project_name_for_edit
from src.services.resumes_service import (
    list_user_resumes,
    get_resume_by_id,
    generate_resume,
    edit_resume,
    delete_resume,
    delete_all_resumes,
    remove_project_from_resume,
    add_project_to_resume,
)
from src.analysis.skills.roles.role_eligibility import get_eligible_roles

router = APIRouter(prefix="/resume", tags=["resume"])

@router.get("", response_model=ApiResponse[ResumeListDTO])
def get_resumes(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_user_resumes(conn, user_id)
    dto = ResumeListDTO(resumes=[ResumeListItemDTO(**row) for row in rows])

    return ApiResponse(success=True, data=dto, error=None)


@router.delete("", response_model=ApiResponse[DeleteResultDTO])
def delete_all_user_resumes(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete all resumes for the current user."""
    count = delete_all_resumes(conn, user_id)
    return ApiResponse(success=True, data=DeleteResultDTO(deleted_count=count), error=None)

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


@router.delete("/{resume_id}", response_model=ApiResponse[None])
def delete_single_resume(
    resume_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete a single resume by ID."""
    deleted = delete_resume(conn, user_id, resume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ApiResponse(success=True, data=None, error=None)


@router.delete("/{resume_id}/projects", response_model=ApiResponse[ResumeDetailDTO | None])
def remove_project_from_resume_endpoint(
    resume_id: int,
    project_name: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Remove a single project from a resume. Deletes the resume if no projects remain."""
    # Check resume exists first so we can give a specific 404 message.
    resume = get_resume_by_id(conn, user_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    result = remove_project_from_resume(conn, user_id, resume_id, project_name)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found in resume")
    if result.get("deleted_resume"):
        return ApiResponse(success=True, data=None, error=None)
    dto = ResumeDetailDTO(**result)
    return ApiResponse(success=True, data=dto, error=None)


@router.post("/{resume_id}/projects", response_model=ApiResponse[ResumeDetailDTO])
def add_project_to_resume_endpoint(
    resume_id: int,
    request: AddProjectRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Add a project to a resume."""
    resume = get_resume_by_id(conn, user_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    result = add_project_to_resume(
        conn, user_id, resume_id, request.project_summary_id
    )
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Project not found or already in resume",
        )
    return ApiResponse(success=True, data=ResumeDetailDTO(**result), error=None)


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

@router.get("/{resume_id}/projects/{project_summary_id}/eligible-roles", response_model=ApiResponse[dict])
def get_resume_project_eligible_roles(
    resume_id: int,
    project_summary_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    resume = get_resume_by_id(conn, user_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    project = next(
        (p for p in resume["projects"] if p["project_summary_id"] == project_summary_id),
        None,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in resume")

    project_type = project.get("project_type")
    project_name = project.get("project_name")

    bucket_scores = None
    if project_name:
        try:
            rows = conn.execute(
                """
                SELECT ps.skill_name, ps.score
                FROM project_skills ps
                JOIN projects p ON p.project_key = ps.project_key
                WHERE ps.user_id = ? AND p.display_name = ?
                """,
                (user_id, project_name),
            ).fetchall()
            if rows:
                bucket_scores = {row[0]: float(row[1]) for row in rows if row[1] is not None}
        except Exception:
            pass

    print(f"[DEBUG] project_name: {project_name}")
    print(f"[DEBUG] project_type: {project_type}")
    print(f"[DEBUG] bucket_scores: {bucket_scores}")
    roles = get_eligible_roles(project_type or "code", bucket_scores)
    return ApiResponse(success=True, data={"roles": roles}, error=None)

@router.post("/{resume_id}/edit", response_model=ApiResponse[ResumeDetailDTO])
def post_resume_edit(
    resume_id: int,
    request: ResumeEditRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    project_name = None
    if request.project_summary_id is not None:
        project_name = resolve_project_name_for_edit(conn, user_id, request.project_summary_id)
        if project_name is None:
            raise HTTPException(status_code=404, detail="Project not found")
    elif request.display_name or request.summary_text or request.contribution_bullets or request.key_role:
        raise HTTPException(status_code=400, detail="project_summary_id is required for project edits")

    try:
        resume = edit_resume(
            conn,
            user_id,
            resume_id,
            project_name=project_name,
            scope=request.scope,
            name=request.name,
            display_name=request.display_name,
            summary_text=request.summary_text,
            contribution_bullets=request.contribution_bullets,
            contribution_edit_mode=request.contribution_edit_mode,
            key_role=request.key_role,
            skill_preferences=request.skill_preferences,
            skill_preferences_reset=request.skill_preferences_reset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not resume:
        raise HTTPException(status_code=404, detail="Resume or project not found")

    dto = ResumeDetailDTO(**resume)
    return ApiResponse(success=True, data=dto, error=None)
