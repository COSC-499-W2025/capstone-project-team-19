from fastapi import APIRouter, Depends, Query
from sqlite3 import Connection
from typing import Optional, Literal

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.skills import (
    SkillPreferencesListDTO,
    SkillWithStatusDTO,
    UpdateSkillPreferencesRequestDTO,
    HighlightedSkillsDTO,
)
from src.services.skill_preferences_service import (
    get_available_skills_with_status,
    update_skill_preferences,
    reset_skill_preferences,
    get_highlighted_skills_for_display,
)

router = APIRouter(prefix="/skills/preferences", tags=["skill-preferences"])


@router.get("", response_model=ApiResponse[SkillPreferencesListDTO])
def get_skill_preferences(
    context: Literal["global", "portfolio", "resume"] = Query(
        "global",
        description="Context for preferences: global, portfolio, or resume"
    ),
    context_id: Optional[int] = Query(
        None,
        description="Resume ID when context is 'resume'"
    ),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    skills = get_available_skills_with_status(conn, user_id, context, context_id)

    dto = SkillPreferencesListDTO(
        skills=[SkillWithStatusDTO(**s) for s in skills],
        context=context,
        context_id=context_id,
    )

    return ApiResponse(success=True, data=dto, error=None)


@router.put("", response_model=ApiResponse[SkillPreferencesListDTO])
def put_skill_preferences(
    request: UpdateSkillPreferencesRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Update global skill preferences."""
    skills = [s.model_dump() for s in request.skills]

    updated = update_skill_preferences(conn=conn, user_id=user_id, skills=skills)

    dto = SkillPreferencesListDTO(
        skills=[SkillWithStatusDTO(**s) for s in updated],
        context="global",
        context_id=None,
    )

    return ApiResponse(success=True, data=dto, error=None)


@router.delete("", response_model=ApiResponse[SkillPreferencesListDTO])
def delete_skill_preferences(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """
    Reset (clear) all global skill preferences.

    After reset, all skills will be shown with default ordering (by score).
    """
    reset_skill_preferences(conn=conn, user_id=user_id)

    # Return current state (all skills with default status)
    skills = get_available_skills_with_status(conn, user_id)

    dto = SkillPreferencesListDTO(
        skills=[SkillWithStatusDTO(**s) for s in skills],
        context="global",
        context_id=None,
    )

    return ApiResponse(success=True, data=dto, error=None)


@router.get("/highlighted", response_model=ApiResponse[HighlightedSkillsDTO])
def get_highlighted_skills(
    context: Literal["global", "portfolio", "resume"] = Query(
        "global",
        description="Context for preferences: global, portfolio, or resume"
    ),
    context_id: Optional[int] = Query(
        None,
        description="Resume ID when context is 'resume'"
    ),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    skills = get_highlighted_skills_for_display(
        conn=conn,
        user_id=user_id,
        context=context,
        context_id=context_id,
    )

    dto = HighlightedSkillsDTO(
        skills=skills,
        context=context,
        context_id=context_id,
    )

    return ApiResponse(success=True, data=dto, error=None)
