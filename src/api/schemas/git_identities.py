from pydantic import BaseModel, Field
from typing import List, Optional


class GitIdentityOptionDTO(BaseModel):
    index: int
    name: Optional[str] = None
    email: Optional[str] = None
    commit_count: int


class GitIdentitiesResponse(BaseModel):
    options: List[GitIdentityOptionDTO]
    selected_indices: List[int]


class GitIdentitiesSelectRequest(BaseModel):
    selected_indices: List[int]
    extra_emails: List[str] = Field(default_factory=list)
