from pydantic import BaseModel
from typing import List, Optional


class PortfolioItemDTO(BaseModel):
    rank: int
    project_name: str
    display_name: str
    score: float
    project_type: str
    project_mode: str
    duration: str
    languages: str
    frameworks: str
    activity: str
    skills: List[str]
    summary_lines: List[str]


class PortfolioDTO(BaseModel):
    items: List[PortfolioItemDTO]