from pydantic import BaseModel
from typing import Any, Dict, Optional, Literal

UploadStatus = Literal[
    "started",
    "parsed",
    "needs_classification",
    "needs_file_roles",
    "needs_summaries",
    "analyzing",
    "done",
    "failed",
]

class UploadDTO(BaseModel):
    upload_id: int
    status: UploadStatus
    zip_name: Optional[str] = None
    state: Dict[str, Any] = {}

class ClassificationsRequest(BaseModel):
    assignments: Dict[str, str]  # project_name -> individual|collaborative

class ProjectTypesRequest(BaseModel):
    project_types: Dict[str, Literal["code", "text"]]  # project_name -> code|text

