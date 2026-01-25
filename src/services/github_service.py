import secrets
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException

from src.integrations.github.github_web_oauth import generate_github_auth_url, exchange_code_for_token
from src.integrations.github.token_store import get_github_token, save_github_token
from src.integrations.github.github_api import list_user_repos
from src.integrations.github.link_repo import get_github_repo_metadata
from src.db.github_repositories import save_project_repo
from src.db.uploads import get_upload_by_id, patch_upload_state


def github_start_connection(
    conn,
    user_id: int,
    upload_id: int,
    project_name: str,
    connect_now: bool
) -> Dict[str, Any]:
    """Start GitHub connection. Returns auth_url if user needs to authorize."""
    if not connect_now:
        patch_upload_state(conn, upload_id, {
            f"github_{project_name}": {"skipped": True}
        })
        return {"auth_url": None, "connected": False}
    
    if get_github_token(conn, user_id):
        patch_upload_state(conn, upload_id, {
            f"github_{project_name}": {"connected": True}
        })
        return {"auth_url": None, "connected": True}
    
    oauth_state = secrets.token_urlsafe(32)
    
    patch_upload_state(conn, upload_id, {
        f"github_{project_name}": {
            "oauth_state": oauth_state,
            "user_id": user_id,
            "upload_id": upload_id,
            "project_name": project_name,
        }
    })
    
    auth_url = generate_github_auth_url(state=oauth_state)
    return {"auth_url": auth_url, "connected": False}


def _find_upload_by_oauth_state(conn, oauth_state: str) -> Optional[Dict[str, Any]]:
    """Find which upload/project this OAuth state belongs to."""
    cursor = conn.execute("""
        SELECT upload_id, user_id, state_json
        FROM uploads
        ORDER BY created_at DESC
        LIMIT 100
    """)
    
    for row in cursor.fetchall():
        upload_id, user_id, state_json = row
        if not state_json:
            continue
        
        try:
            state = json.loads(state_json)
            for key, value in state.items():
                if key.startswith("github_") and isinstance(value, dict):
                    if value.get("oauth_state") == oauth_state:
                        return {
                            "user_id": user_id,
                            "upload_id": upload_id,
                            "project_name": key.replace("github_", ""),
                        }
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return None


def github_handle_callback(conn, code: str, state: Optional[str] = None) -> Dict[str, Any]:
    """Handle GitHub redirect after user authorizes. Saves the token."""
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")
    
    state_info = _find_upload_by_oauth_state(conn, state)
    if not state_info:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    
    token_response = exchange_code_for_token(code, state)
    if not token_response or "access_token" not in token_response:
        raise HTTPException(status_code=400, detail="Failed to get token")

    save_github_token(conn, state_info["user_id"], token_response["access_token"])
    
    patch_upload_state(conn, state_info["upload_id"], {
        f"github_{state_info['project_name']}": {"connected": True}
    })
    
    return {"success": True, **state_info}


def github_list_repos(conn, user_id: int) -> Optional[list[str]]:
    """Get list of user's repos. Returns None if not connected."""
    token = get_github_token(conn, user_id)
    if not token:
        return None
    return list_user_repos(token)


def github_link_repo(conn, user_id: int, project_name: str, repo_full_name: str) -> Optional[Dict[str, Any]]:
    """Link a repo to a project. Reuses existing function."""
    token = get_github_token(conn, user_id)
    if not token:
        return None
    
    parts = repo_full_name.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None 

    repo_url, repo_owner, repo_name, repo_id, default_branch = get_github_repo_metadata(
        user_id, project_name, repo_full_name, token
    )

    save_project_repo(
        conn, user_id, project_name, repo_url, repo_full_name,
        repo_owner, repo_name, repo_id, default_branch, provider="github"
    )
    
    return {"success": True, "repo_full_name": repo_full_name}