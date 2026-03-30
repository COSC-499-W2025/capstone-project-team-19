from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse, DeleteResultDTO
from src.api.schemas.resumes import ResumeListDTO, ResumeListItemDTO, ResumeDetailDTO, ResumeGenerateRequestDTO, ResumeEditRequestDTO, AddProjectRequestDTO, ResumeSkillStatusDTO, ResumeSkillListDTO
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
import json
from src.db.projects import get_project_key
from src.db.resumes import get_resume_snapshot
from src.db.skill_preferences import get_project_skill_names
from src.services.skill_preferences_service import get_available_skills_with_status

# Must match the mapping in src/export/resume_helpers.py filter_skills_by_highlighted
# and src/menu/resume/helpers.py _filter_skills_by_highlighted exactly.
_SKILL_DISPLAY_NAMES = {
    # technical skills
    "architecture_and_design": "Architecture & design",
    "data_structures": "Data structures",
    "frontend_skills": "Frontend development",
    "object_oriented_programming": "Object-oriented programming",
    "security_and_error_handling": "Security & error handling",
    "testing_and_ci": "Testing & CI",
    "algorithms": "Algorithms",
    "backend_development": "Backend development",
    "clean_code_and_quality": "Clean code & quality",
    "devops_and_ci_cd": "DevOps & CI/CD",
    "api_and_backend": "API & backend",
    # writing skills
    "clarity": "Clear communication",
    "structure": "Structured writing",
    "vocabulary": "Strong vocabulary",
    "argumentation": "Analytical writing",
    "depth": "Critical thinking",
    "process": "Revision & editing",
    "planning": "Planning & organization",
    "research": "Research integration",
    "data_collection": "Data collection",
    "data_analysis": "Data analysis",
}


def _skill_display_name(skill_name: str) -> str:
    if skill_name in _SKILL_DISPLAY_NAMES:
        return _SKILL_DISPLAY_NAMES[skill_name]
    return skill_name.replace("_", " ").title()

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

@router.get("/{resume_id}/skills", response_model=ApiResponse[ResumeSkillListDTO])
def get_resume_skills(
    resume_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Return skills present in this resume with their preference status."""
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Derive skills from the live project_skills table so the editor always
    # reflects the actual resume projects, not a stale / previously-filtered snapshot.
    try:
        snapshot = json.loads(record.get("resume_json") or "{}")
    except Exception:
        snapshot = {}
    project_names = [p.get("project_name") for p in snapshot.get("projects", []) if p.get("project_name")]
    resume_raw_keys: set[str] = set()
    for name in project_names:
        pk = get_project_key(conn, user_id, name)
        if pk is not None:
            resume_raw_keys.update(get_project_skill_names(conn, user_id, pk))

    # Get preference status for all user skills, then filter to resume-only
    all_skills = get_available_skills_with_status(
        conn, user_id, context="resume", context_id=resume_id
    )
    skills = [
        ResumeSkillStatusDTO(
            skill_name=s["skill_name"],
            display_name=_skill_display_name(s["skill_name"]),
            is_highlighted=bool(s["is_highlighted"]),
            display_order=s.get("display_order"),
        )
        for s in all_skills
        if s["skill_name"] in resume_raw_keys
    ]
    return ApiResponse(success=True, data=ResumeSkillListDTO(skills=skills), error=None)


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
