from typing import List, Optional
from pydantic import BaseModel, Field

class SkillEventDTO(BaseModel):
    skill_name: str
    level: str
    score: float
    project_name: str
    actual_activity_date: Optional[str] = None
    recorded_at: Optional[str] = None

class SkillsListDTO(BaseModel):
    skills: List[SkillEventDTO]

class SkillPreferenceDTO(BaseModel):
    skill_name: str
    is_highlighted: bool = True
    display_order: Optional[int] = None

class SkillWithStatusDTO(BaseModel):
    skill_name: str
    is_highlighted: bool = True
    display_order: Optional[int] = None
    project_count: int = 0
    max_score: float = 0.0

class SkillPreferencesListDTO(BaseModel):
    skills: List[SkillWithStatusDTO]
    context: str = "global"
    context_id: Optional[int] = None

class UpdateSkillPreferencesRequestDTO(BaseModel):
    skills: List[SkillPreferenceDTO] = Field(
        ...,
        description="List of skill preferences to update"
    )

class HighlightedSkillsDTO(BaseModel):
    skills: List[str]
    context: str = "global"
    context_id: Optional[int] = None