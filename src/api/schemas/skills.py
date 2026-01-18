from typing import List, Optional
from pydantic import BaseModel

class SkillEventDTO(BaseModel):
    skill_name: str
    level: str
    score: float
    project_name: str
    actual_activity_date: Optional[str] = None
    recorded_at: Optional[str] = None

class SkillsListDTO(BaseModel):
    skills: List[SkillEventDTO]