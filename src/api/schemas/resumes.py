from pydantic import BaseModel
from typing import List, Optional

class ResumeListItemDTO(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None

class ResumeListDTO(BaseModel):
    resumes: List[ResumeListItemDTO]