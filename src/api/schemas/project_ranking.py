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


class FileDiffDTO(BaseModel):
    filesAdded: List[str] = []
    filesModified: List[str] = []
    filesRemoved: List[str] = []
    unchangedCount: int = 0


class SkillChangeDTO(BaseModel):
    skill_name: str
    level: str
    score: float
    prev_score: Optional[float] = None


class SkillProgressionDTO(BaseModel):
    newSkills: List[SkillChangeDTO] = []
    improvedSkills: List[SkillChangeDTO] = []
    declinedSkills: List[SkillChangeDTO] = []
    removedSkills: List[SkillChangeDTO] = []


class VersionDiffDTO(BaseModel):
    linesAdded: Optional[int] = None
    linesModified: Optional[int] = None
    linesRemoved: Optional[int] = None
    files: Optional[FileDiffDTO] = None


class EvolutionVersionDTO(BaseModel):
    versionId: str
    date: str
    summary: str
    diff: Optional[VersionDiffDTO] = None
    skills: List[str] = []
    skillsDetail: List[Dict[str, Any]] = []
    skillProgression: Optional[SkillProgressionDTO] = None
    languages: List[str] = []
    frameworks: List[str] = []
    avgComplexity: Optional[float] = None
    totalFiles: Optional[int] = None


class ProjectEvolutionDTO(BaseModel):
    projectId: str
    title: str
    versions: List[EvolutionVersionDTO]
