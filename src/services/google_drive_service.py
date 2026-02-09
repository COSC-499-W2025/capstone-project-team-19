"""
Google Drive service layer for API endpoints.
Orchestrates OAuth flow, token management, file listing, and file linking.
"""

import secrets
import json
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

from src.integrations.google_drive.google_drive_web_oauth import (generate_google_auth_url,exchange_code_for_tokens,)
from src.integrations.google_drive.token_store import (get_google_drive_token,save_google_drive_tokens,)
from src.db.drive_files import store_file_link
from src.db.uploads import patch_upload_state


def drive_start_connection(
    conn,
    user_id: int,
    upload_id: int,
    project_name: str,
    connect_now: bool,
) -> Dict[str, Any]:
    """Start Google Drive connection flow for a project."""
    if not connect_now:
        patch_upload_state(conn, upload_id, {
            f"drive_{project_name}": {"skipped": True}
        })
        return {"auth_url": None, "connected": False}

    if get_google_drive_token(conn, user_id):
        patch_upload_state(conn, upload_id, {
            f"drive_{project_name}": {"connected": True}
        })
        return {"auth_url": None, "connected": True}

    oauth_state = secrets.token_urlsafe(32)

    patch_upload_state(conn, upload_id, {
        f"drive_{project_name}": {
            "oauth_state": oauth_state,
            "user_id": user_id,
            "upload_id": upload_id,
            "project_name": project_name,
        }
    })

    auth_url = generate_google_auth_url(state=oauth_state)
    return {"auth_url": auth_url, "connected": False}


def _find_upload_by_drive_oauth_state(conn, oauth_state: str) -> Optional[Dict[str, Any]]:
    """ Find which upload/project this OAuth state belongs to."""
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
                if key.startswith("drive_") and isinstance(value, dict):
                    if value.get("oauth_state") == oauth_state:
                        return {
                            "user_id": user_id,
                            "upload_id": upload_id,
                            "project_name": key.replace("drive_", "", 1),
                        }
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return None


def drive_handle_callback(conn, code: str, state: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle Google OAuth redirect after user authorizes.

    Exchanges the authorization code for tokens, saves them, and marks
    the upload/project as connected.
    """
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    state_info = _find_upload_by_drive_oauth_state(conn, state)
    if not state_info:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_response = exchange_code_for_tokens(code)
    if not token_response or "access_token" not in token_response:
        raise HTTPException(status_code=400, detail="Failed to get token from Google")

    save_google_drive_tokens(
        conn,
        state_info["user_id"],
        access_token=token_response["access_token"],
        refresh_token=token_response.get("refresh_token"),
        expires_at=token_response.get("expires_in"),
    )

    patch_upload_state(conn, state_info["upload_id"], {
        f"drive_{state_info['project_name']}": {"connected": True}
    })

    return {"success": True, **state_info}


def drive_list_files(conn, user_id: int) -> Optional[List[Dict[str, str]]]:
    """List the user's Google Drive files."""
    token = get_google_drive_token(conn, user_id)
    if not token:
        return None
    return _fetch_drive_files(token)


def _fetch_drive_files(token: str) -> List[Dict[str, str]]:
    """ Call the Google Drive API to list the user's supported files. """
    import requests

    headers = {"Authorization": f"Bearer {token}"}
    supported_mimes = [
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.spreadsheet",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
    ]
    mime_conditions = " or ".join([f"mimeType='{m}'" for m in supported_mimes])
    query = f"trashed=false and ({mime_conditions})"

    all_files = []
    page_token = None

    while True:
        params = {
            "pageSize": 100,
            "fields": "nextPageToken, files(id, name, mimeType)",
            "q": query,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            headers=headers,
            params=params,
        )

        if resp.status_code != 200:
            print(f"[Google Drive] Failed to list files: {resp.status_code} - {resp.text}")
            return []

        data = resp.json()
        all_files.extend(data.get("files", []))

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_files


def drive_link_files(conn,user_id: int,project_name: str,links: List[Dict[str, str]],) -> Optional[Dict[str, Any]]:
    """ Link Drive files to a project's local files. """
    token = get_google_drive_token(conn, user_id)
    if not token:
        return None

    for link in links:
        store_file_link(
            conn,
            user_id=user_id,
            project_name=project_name,
            local_file_name=link["local_file_name"],
            drive_file_id=link["drive_file_id"],
            drive_file_name=link.get("drive_file_name"),
            mime_type=link.get("mime_type"),
            status="manual_selected",
        )

    return {
        "success": True,
        "project_name": project_name,
        "files_linked": len(links),
    }
