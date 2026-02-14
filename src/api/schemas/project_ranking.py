from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


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


class TopProjectItemDTO(BaseModel):
    projectId: str
    title: str
    rankScore: float
    summarySnippet: Optional[str] = None
    versionCount: int = 0


class TopProjectsDTO(BaseModel):
    topProjects: List[TopProjectItemDTO]


class VersionDiffDTO(BaseModel):
    added: Optional[int] = None
    modified: Optional[int] = None
    removed: Optional[int] = None


class EvolutionVersionDTO(BaseModel):
    versionId: str
    date: str
    summary: str
    diff: Optional[VersionDiffDTO] = None
    skills: List[str] = []
    skillsDetail: List[Dict[str, Any]] = []


class ProjectEvolutionDTO(BaseModel):
    projectId: str
    title: str
    versions: List[EvolutionVersionDTO]