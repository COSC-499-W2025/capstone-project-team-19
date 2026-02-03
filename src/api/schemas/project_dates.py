from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from src.services.project_dates_service import validate_manual_date_range

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

    @field_validator("end_date")
    @classmethod
    def _validate_range(cls, v, info):
        # NOTE: This validator only triggers if end_date is present in input.
        # We'll validate again in the route based on which fields were provided.
        start_date = info.data.get("start_date")
        validate_manual_date_range(start_date, v)
        return v

class ResetProjectDatesResultDTO(BaseModel):
    cleared_count: int
