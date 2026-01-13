from pydantic import BaseModel
from typing import List, Optional

class ProjectListItemDTO(BaseModel):
    project_summary_id: int
    project_name: str
    project_type: Optional[str] = None
    project_mode: Optional[str] = None
    created_at: Optional[str] = None

class ProjectListDTO(BaseModel):
    projects: List[ProjectListItemDTO]