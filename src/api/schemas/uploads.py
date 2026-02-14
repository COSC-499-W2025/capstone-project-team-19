from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional, Literal, List

UploadStatus = Literal[
    "started",
    "parsed",
    "needs_dedup",
    "needs_classification",
    "needs_project_types",
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
    project_types: Dict[str, str]  # project_name -> code|text

DedupDecision = Literal["skip", "new_project", "new_version"]

class DedupResolveRequestDTO(BaseModel):
    decisions: Dict[str, DedupDecision]

class UploadFileItemDTO(BaseModel):
    relpath: str
    file_name: str
    file_type: Optional[str] = None
    extension: Optional[str] = None
    size_bytes: Optional[int] = None

class UploadProjectFilesDTO(BaseModel):
    project_key: Optional[int] = None  # Stable identifier for API calls
    version_key: Optional[int] = None  # Identifies this upload's version for metrics
    project_name: str  # Display only
    all_files: List[UploadFileItemDTO]
    text_files: List[UploadFileItemDTO]
    csv_files: List[UploadFileItemDTO]

class MainFileRequestDTO(BaseModel):
    relpath: str
    

class SupportingFilesRequestDTO(BaseModel):
    relpaths: List[str] = []


class KeyRoleRequestDTO(BaseModel):
    key_role: str = Field(..., min_length=1, max_length=120)

    @field_validator("key_role")
    @classmethod
    def normalize_key_role(cls, value: str) -> str:
        normalized = " ".join((value or "").split())
        if not normalized:
            raise ValueError("key_role must not be blank")
        return normalized


class MainFileSectionDTO(BaseModel):
    id: int
    title: str
    preview: str
    content: str
    is_truncated: bool = False

class MainFileSectionsResponseDTO(BaseModel):
    project_key: Optional[int] = None  # Stable identifier for API calls
    version_key: Optional[int] = None  # Identifies this upload's version
    project_name: str  # Display only
    main_file: str
    sections: List[MainFileSectionDTO]

class ContributedSectionsRequestDTO(BaseModel):
    selected_section_ids: List[int]
