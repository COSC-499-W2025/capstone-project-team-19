import os
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlite3 import Connection

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.services.github_service import github_handle_callback
from src.api.schemas.github import (
    GitHubStartRequest, GitHubStartResponse, 
    GitHubReposResponse, GitHubRepoDTO, GitHubLinkRequest
)
from src.services.github_service import (github_start_connection, github_list_repos, github_link_repo)
from src.services.uploads_service import get_upload_status

router = APIRouter(tags=["github"])


_FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")


@router.get("/auth/github/callback")
def get_github_callback(
    code: str = Query(...),
    state: str = Query(None),
    conn: Connection = Depends(get_db),
):
    """OAuth callback endpoint for GitHub. Redirects to frontend setup page on success."""
    try:
        result = github_handle_callback(conn, code, state)
        upload_id = result.get("upload_id")
        params = {"github": "success"}
        if upload_id is not None:
            params["uploadId"] = str(upload_id)
        redirect_url = f"{_FRONTEND_BASE_URL}/upload/setup?{urlencode(params)}"
        return RedirectResponse(url=redirect_url, status_code=302)
    except HTTPException as exc:
        params = {"github": "error", "message": str(exc.detail)}
        redirect_url = f"{_FRONTEND_BASE_URL}/upload/setup?{urlencode(params)}"
        return RedirectResponse(url=redirect_url, status_code=302)
    except Exception as e:
        params = {"github": "error", "message": str(e)}
        redirect_url = f"{_FRONTEND_BASE_URL}/upload/setup?{urlencode(params)}"
        return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/projects/upload/{upload_id}/projects/{project}/github/start", response_model=ApiResponse[GitHubStartResponse])
def post_github_start(
    upload_id: int,
    project: str,
    body: GitHubStartRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Start GitHub connection flow for a project."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    result = github_start_connection(conn, user_id, upload_id, project, body.connect_now)
    
    return ApiResponse(
        success=True,
        data=GitHubStartResponse(auth_url=result.get("auth_url")),
        error=None
    )


@router.get("/projects/upload/{upload_id}/projects/{project}/github/repos", response_model=ApiResponse[GitHubReposResponse])
def get_github_repos(
    upload_id: int,
    project: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """List user's GitHub repositories."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    repos = github_list_repos(conn, user_id)
    if repos is None:
        raise HTTPException(
            status_code=401,
            detail="GitHub not connected. Please connect GitHub first."
        )
    
    repo_dtos = [GitHubRepoDTO(full_name=repo) for repo in repos]
    
    return ApiResponse(
        success=True,
        data=GitHubReposResponse(repos=repo_dtos),
        error=None
    )


@router.post("/projects/upload/{upload_id}/projects/{project}/github/link", response_model=ApiResponse[dict])
def post_github_link(
    upload_id: int,
    project: str,
    body: GitHubLinkRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Link a GitHub repository to a project."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    result = github_link_repo(conn, user_id, upload_id, project, body.repo_full_name)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to link repository. Check that GitHub is connected and repo name is valid."
        )
    
    return ApiResponse(success=True, data=result, error=None)
