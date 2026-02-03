from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ProjectDateSource = Literal["AUTO", "MANUAL"]

class ProjectDatesItemDTO(BaseModel):
    project_summary_id: int
    project_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: ProjectDateSource
    manual_start_date: Optional[str] = None
    manual_end_date: Optional[str] = None

class ProjectDatesListDTO(BaseModel):
    projects: List[ProjectDatesItemDTO]

class PatchProjectDatesRequestDTO(BaseModel):
    """
    Patch manual project dates.

    - Omit a field to keep current value.
    - Provide null to clear that side.
    """

    start_date: Optional[str] = Field(
        default=None,
        description="Manual start date (YYYY-MM-DD). Omit to keep current. Use null to clear.",
    )

    end_date: Optional[str] = Field(
        default=None,
        description="Manual end date (YYYY-MM-DD). Omit to keep current. Use null to clear.",
    )

class ResetProjectDatesResultDTO(BaseModel):
    cleared_count: int
