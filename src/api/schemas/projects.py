from pydantic import BaseModel
from typing import Any, List, Optional, Dict

class ProjectListItemDTO(BaseModel):
    project_summary_id: int
    project_key: Optional[int] = None
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    created_at: Optional[str] = None

class ProjectListDTO(BaseModel):
    projects: List[ProjectListItemDTO]

class ProjectDetailDTO(BaseModel):
    project_summary_id: int
    project_key: Optional[int] = None
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    created_at: Optional[str] = None
    summary_text: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    skills: List[str] = []
    metrics: Dict[str, Any] = {}
    contributions: Dict[str, Any] = {}
