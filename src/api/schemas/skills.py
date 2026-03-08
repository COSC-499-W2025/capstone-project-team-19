from typing import Dict, List, Optional
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

class SkillPreferenceDTO(BaseModel):
    skill_name: str
    is_highlighted: Optional[bool] = True
    display_order: Optional[int] = None
class TimelineEventDTO(BaseModel):
    skill_name: str
    level: str
    score: float
    project_name: str

class CumulativeSkillDTO(BaseModel):
    cumulative_score: float
    projects: List[str]

class DateGroupDTO(BaseModel):
    date: str
    events: List[TimelineEventDTO]
    cumulative_skills: Dict[str, CumulativeSkillDTO]

class CurrentTotalDTO(BaseModel):
    cumulative_score: float
    projects: List[str]
    skill_type: Optional[str] = None  # "text" | "code" | "unknown"

class TimelineSummaryDTO(BaseModel):
    total_skills: int
    total_projects: int
    date_range: Dict[str, Optional[str]]
    skill_names: List[str]

class SkillTimelineDTO(BaseModel):
    dated: List[DateGroupDTO]
    undated: List[TimelineEventDTO]
    current_totals: Dict[str, CurrentTotalDTO]
    summary: TimelineSummaryDTO
