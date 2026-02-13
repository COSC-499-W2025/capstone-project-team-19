from __future__ import annotations

import sqlite3
from fastapi import HTTPException

from src.db.uploads import get_upload_by_id, patch_upload_state


_ALLOWED_STATUSES = {"needs_summaries", "analyzing", "done"}


def set_manual_project_summary(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    summary_text: str,
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}
    _require_project_in_upload(state, project_name)

    text = (summary_text or "").strip() or "[No manual project summary provided]"

    manual = dict(state.get("manual_project_summaries") or {})
    manual[project_name] = text

    new_state = patch_upload_state(
        conn,
        upload["upload_id"],
        patch={"manual_project_summaries": manual},
        status=upload["status"],
    )

    return {
        "upload_id": upload["upload_id"],
        "status": upload["status"],
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def set_manual_contribution_summary(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    manual_contribution_summary: str,
    key_role: str | None = None,
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}
    _require_project_in_upload(state, project_name)

    desc = (manual_contribution_summary or "").strip() or "[No description provided]"

    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(project_name) or {})
    proj["manual_contribution_summary"] = desc

    if key_role is not None:
        kr = (key_role or "").strip()
        if kr:
            proj["key_role"] = kr

    contributions[project_name] = proj

    new_state = patch_upload_state(
        conn,
        upload["upload_id"],
        patch={"contributions": contributions},
        status=upload["status"],
    )

    return {
        "upload_id": upload["upload_id"],
        "status": upload["status"],
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


# -----------------------
# helpers
# -----------------------
def _require_upload(conn: sqlite3.Connection, user_id: int, upload_id: int) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def _require_status(upload: dict) -> None:
    status = upload.get("status")
    if status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=409, detail=f"Upload not ready for summaries (status={status})")


def _require_project_in_upload(state: dict, project_name: str) -> None:
    layout = state.get("layout") or {}
    known = set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])
    if project_name not in known:
        raise HTTPException(
            status_code=404,
            detail={"message": "Project not found in this upload", "project_name": project_name},
        )