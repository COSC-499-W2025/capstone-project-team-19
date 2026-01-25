from pydantic import BaseModel
from typing import List, Optional

class GitHubStartRequest(BaseModel):
    connect_now: bool

class GitHubStartResponse(BaseModel):
    auth_url: Optional[str] = None

class GitHubRepoDTO(BaseModel):
    full_name: str

class GitHubReposResponse(BaseModel):
    repos: List[GitHubRepoDTO]

class GitHubLinkRequest(BaseModel):
    repo_full_name: str