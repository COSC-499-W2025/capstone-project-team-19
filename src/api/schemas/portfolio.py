from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional


class PortfolioProjectDTO(BaseModel):
    project_summary_id: Optional[int] = None  # Preferred identifier for edits
    project_name: str
    display_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    score: float = 0.0
    duration: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    activity: Optional[str] = None
    skills: List[str] = []
    summary_text: Optional[str] = None
    contribution_bullets: List[str] = []


class PortfolioDetailDTO(BaseModel):
    projects: List[PortfolioProjectDTO] = []
    rendered_text: Optional[str] = None


class PortfolioGenerateRequestDTO(BaseModel):
    name: str = Field(..., max_length=200)


class PortfolioEditRequestDTO(BaseModel):
    project_summary_id: Optional[int] = None  # Preferred over project_name for edits
    project_name: Optional[str] = Field(None, max_length=200)  # Deprecated: use project_summary_id instead
    scope: Optional[Literal["portfolio_only", "global"]] = "portfolio_only"
    display_name: Optional[str] = Field(None, max_length=200)
    summary_text: Optional[str] = Field(None, max_length=5000)
    contribution_bullets: Optional[List[str]] = None
    name: Optional[str] = Field(default="Portfolio", max_length=200)

    @model_validator(mode="after")
    def require_project_identifier(self):
        if self.project_summary_id is None and not self.project_name:
            raise ValueError("Either project_summary_id or project_name must be provided")
        return self