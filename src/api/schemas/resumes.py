from pydantic import BaseModel
from typing import Any, List, Optional, Dict, Literal
from src.api.schemas.skills import SkillPreferenceDTO

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
    key_role: Optional[str] = None
    contribution_bullets: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AggregatedSkillsDTO(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    technical_skills: List[str] = []
    writing_skills: List[str] = []
    advanced: List[str] = []
    intermediate: List[str] = []
    beginner: List[str] = []


class ResumeContactDTO(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None


class ResumeEducationEntryDTO(BaseModel):
    entry_id: int
    entry_type: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None


class ResumeExperienceEntryDTO(BaseModel):
    entry_id: int
    role: Optional[str] = None
    company: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None


class ResumePreviewDTO(BaseModel):
    display_name: str
    contact: ResumeContactDTO
    profile_text: Optional[str] = None
    education_entries: List[ResumeEducationEntryDTO] = []
    experience_entries: List[ResumeExperienceEntryDTO] = []
    certificate_entries: List[ResumeEducationEntryDTO] = []

class ResumeOnePageStatusDTO(BaseModel):
    fits_one_page: bool
    page_count: int
    overflow_detected: bool
    overflow_mode: Literal["none", "block", "warn"]
    overflow_reason: Optional[str] = None
    has_manual_project_edits: bool = False

class ResumeDetailDTO(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None
    projects: List[ResumeProjectDTO] = []
    aggregated_skills: AggregatedSkillsDTO = AggregatedSkillsDTO()
    rendered_text: Optional[str] = None
    one_page_status: ResumeOnePageStatusDTO
    preview: ResumePreviewDTO

class ResumeGenerateRequestDTO(BaseModel):
    name: str
    project_ids: Optional[List[int]] = None

class AddProjectRequestDTO(BaseModel):
    project_summary_id: int

class ResumeEditRequestDTO(BaseModel):
    name: Optional[str] = None
    project_summary_id: Optional[int] = None  # Required when editing project fields; use from resume detail response
    scope: Optional[Literal["resume_only", "global"]] = None
    display_name: Optional[str] = None
    summary_text: Optional[str] = None
    contribution_bullets: Optional[List[str]] = None
    contribution_edit_mode: Optional[Literal["append", "replace"]] = "replace"
    key_role: Optional[str] = None
    skill_preferences: Optional[List[SkillPreferenceDTO]] = None
    skill_preferences_reset: Optional[bool] = False


class ResumeSkillStatusDTO(BaseModel):
    skill_name: str
    display_name: str
    is_highlighted: bool
    display_order: Optional[int] = None


class ResumeSkillListDTO(BaseModel):
    skills: List[ResumeSkillStatusDTO]