from pydantic import BaseModel
from typing import List, Optional


class PublicProjectListItemDTO(BaseModel):
    project_summary_id: int
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    created_at: Optional[str] = None


class PublicProjectListDTO(BaseModel):
    projects: List[PublicProjectListItemDTO]


class PublicProjectDetailDTO(BaseModel):
    project_summary_id: int
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    created_at: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    summary_text: Optional[str] = None
    contribution_summary: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    skills: List[str] = []


class PublicRankingItemDTO(BaseModel):
    rank: int
    project_summary_id: int
    project_name: str


class PublicRankingDTO(BaseModel):
    rankings: List[PublicRankingItemDTO]


class PublicResumeProjectDTO(BaseModel):
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    summary_text: Optional[str] = None
    skills: List[str] = []
    key_role: Optional[str] = None
    contribution_bullets: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PublicAggregatedSkillsDTO(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    technical_skills: List[str] = []
    writing_skills: List[str] = []


class PublicResumeDetailDTO(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None
    projects: List[PublicResumeProjectDTO] = []
    aggregated_skills: PublicAggregatedSkillsDTO = PublicAggregatedSkillsDTO()
    rendered_text: Optional[str] = None


class PublicSkillDTO(BaseModel):
    skill_name: str
    level: str
    project_name: str


class PublicSkillsListDTO(BaseModel):
    skills: List[PublicSkillDTO]
