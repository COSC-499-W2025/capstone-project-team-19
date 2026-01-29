from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional


class ProjectRankingItemDTO(BaseModel):
    rank: int
    project_summary_id: int
    project_name: str
    score: float
    manual_rank: Optional[int] = None


class ProjectRankingDTO(BaseModel):
    rankings: List[ProjectRankingItemDTO]


class ReplaceProjectRankingRequestDTO(BaseModel):
    project_ids: List[int]


class PatchProjectRankingRequestDTO(BaseModel):
    # Required field: clients must explicitly send {"rank": <int>} or {"rank": null}
    rank: Optional[int]

