from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ProjectFeedbackItemDTO(BaseModel):
    feedback_id: Optional[int] = None
    project_type: Optional[str] = None  # code or text
    skill_name: str
    file_name: str = ""
    criterion_key: str
    criterion_label: str
    expected: Optional[str] = None
    observed: Dict[str, Any] = Field(default_factory=dict)
    suggestion: Optional[str] = None
    generated_at: Optional[str] = None


class ProjectFeedbackDTO(BaseModel):
    project_id: int
    project_name: str
    feedback: List[ProjectFeedbackItemDTO] = Field(default_factory=list)