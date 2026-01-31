from pydantic import BaseModel
from typing import List


class FeedbackSuggestionDTO(BaseModel):
    skill_name: str
    suggestion: str


class ProjectFeedbackDTO(BaseModel):
    project_summary_id: int
    project_name: str
    feedback: List[FeedbackSuggestionDTO]


class ProjectsFeedbackDTO(BaseModel):
    projects: List[ProjectFeedbackDTO]


class ProjectsFeedbackByIdsDTO(BaseModel):
    requested_project_ids: List[int]
    missing_project_ids: List[int]
    projects: List[ProjectFeedbackDTO]

