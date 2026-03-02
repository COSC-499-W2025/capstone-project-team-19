from pydantic import BaseModel
from typing import Any, List, Optional, Dict, Literal

class ResumeListItemDTO(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None

class ResumeListDTO(BaseModel):
    resumes: List[ResumeListItemDTO]

class ResumeProjectDTO(BaseModel):
    project_summary_id: Optional[int] = None  # Preferred identifier for edits
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    summary_text: Optional[str] = None
    skills: List[str] = []
    text_type: Optional[str] = None
    contribution_percent: Optional[float] = None
    activities: List[Dict[str, Any]] = []

class AggregatedSkillsDTO(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    technical_skills: List[str] = []
    writing_skills: List[str] = []

class ResumeDetailDTO(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None
    projects: List[ResumeProjectDTO] = []
    aggregated_skills: AggregatedSkillsDTO = AggregatedSkillsDTO()
    rendered_text: Optional[str] = None

class ResumeGenerateRequestDTO(BaseModel):
    name: str
    project_ids: Optional[List[int]] = None

class ResumeEditRequestDTO(BaseModel):
    name: Optional[str] = None
    project_summary_id: Optional[int] = None  # Required when editing project fields; use from resume detail response
    scope: Optional[Literal["resume_only", "global"]] = None
    display_name: Optional[str] = None
    summary_text: Optional[str] = None
    contribution_bullets: Optional[List[str]] = None
    contribution_edit_mode: Optional[Literal["append", "replace"]] = "replace"
    key_role: Optional[str] = None