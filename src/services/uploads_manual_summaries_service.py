from __future__ import annotations

import sqlite3
from fastapi import HTTPException

from src.db.uploads import get_upload_by_id, patch_upload_state


_ALLOWED_STATUSES = {"needs_summaries", "analyzing", "done"}


def set_manual_project_summary(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_key: int,
    summary_text: str,
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}
    _require_project_key_in_upload(state, project_key)

    text = (summary_text or "").strip() or "[No manual project summary provided]"

    manual = dict(state.get("manual_project_summaries") or {})
    manual[str(project_key)] = text

    patched_state = patch_upload_state(
        conn,
        upload["upload_id"],
        patch={"manual_project_summaries": manual},
        status=upload["status"],
    )

    new_status = _maybe_advance_status_after_summaries(upload["status"], patched_state)

    if new_status != upload["status"]:
        patched_state = patch_upload_state(
            conn,
            upload["upload_id"],
            patch={},
            status=new_status,
        )

    return {
        "upload_id": upload["upload_id"],
        "status": new_status,
        "zip_name": upload.get("zip_name"),
        "state": patched_state,
    }


def set_manual_contribution_summary(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_key: int,
    manual_contribution_summary: str,
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}
    _require_project_key_in_upload(state, project_key)

    desc = (manual_contribution_summary or "").strip() or "[No description provided]"

    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(str(project_key)) or {})
    proj["manual_contribution_summary"] = desc
    contributions[str(project_key)] = proj

    patched_state = patch_upload_state(
        conn,
        upload["upload_id"],
        patch={"contributions": contributions},
        status=upload["status"],
    )

    new_status = _maybe_advance_status_after_summaries(upload["status"], patched_state)

    if new_status != upload["status"]:
        patched_state = patch_upload_state(
            conn,
            upload["upload_id"],
            patch={},
            status=new_status,
        )

    return {
        "upload_id": upload["upload_id"],
        "status": new_status,
        "zip_name": upload.get("zip_name"),
        "state": patched_state,
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


def _require_project_key_in_upload(state: dict, project_key: int) -> None:
    required = state.get("summaries_required_project_keys") or []
    required_set = set(str(x) for x in required)

    # If you didn’t store the required list yet, we fail loudly so it doesn’t silently pass wrong keys.
    if not required_set:
        raise HTTPException(
            status_code=409,
            detail="Upload missing summaries_required_project_keys (wizard transition must set this).",
        )

    if str(project_key) not in required_set:
        raise HTTPException(
            status_code=404,
            detail={"message": "Project not found in this upload summaries scope", "project_key": project_key},
        )


def _maybe_advance_status_after_summaries(current_status: str, state: dict) -> str:
    # Only advance from needs_summaries. If you're already analyzing/done, keep it.
    if current_status != "needs_summaries":
        return current_status

    required = state.get("summaries_required_project_keys") or []
    required_keys = [str(x) for x in required]

    manual_projects = state.get("manual_project_summaries") or {}
    contributions = state.get("contributions") or {}

    for pk in required_keys:
        proj_summary_ok = isinstance(manual_projects.get(pk), str) and manual_projects.get(pk).strip() != ""
        contrib_obj = contributions.get(pk) or {}
        contrib_summary_ok = isinstance(contrib_obj.get("manual_contribution_summary"), str) and contrib_obj.get("manual_contribution_summary").strip() != ""
        if not (proj_summary_ok and contrib_summary_ok):
            return current_status

    # All required project keys have both summaries
    return "analyzing"