from fastapi import APIRouter, Depends
from sqlite3 import Connection

from src.api.dependencies import get_db
from src.api.auth.deps import get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.skills import SkillEventDTO, SkillsListDTO
from src.services.skills_service import get_user_skills

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("", response_model=ApiResponse[SkillsListDTO])
def get_skills(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    skills = get_user_skills(conn, user_id)
    dto = SkillsListDTO(skills=[SkillEventDTO(**s) for s in skills])
    
    return ApiResponse(success=True, data=dto, error=None)