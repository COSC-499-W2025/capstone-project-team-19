from __future__ import annotations

import sqlite3
from typing import Iterable

from fastapi import HTTPException

from src.db.uploads import get_upload_by_id, patch_upload_state
from src.services.uploads_service import list_project_files
from src.services.uploads_file_roles_util import safe_relpath


_ALLOWED_STATUSES = {"needs_file_roles", "needs_summaries", "analyzing", "done"}


def set_project_supporting_text_files(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    relpaths: list[str],
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}
    main_file = _get_main_file_relpath(state, project_name)

    # Reuse existing file listing logic for validation + allowed candidates
    files_payload = list_project_files(conn, user_id, upload_id, project_name)
    allowed = _allowed_supporting_text_relpaths(files_payload, main_file)

    selected = _normalize_relpaths(relpaths)
    invalid = sorted([p for p in selected if p not in allowed])
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "One or more relpaths are not valid supporting TEXT files for this project",
                "invalid_relpaths": invalid,
            },
        )

    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(project_name) or {})
    proj["supporting_text_relpaths"] = sorted(selected)
    contributions[project_name] = proj

    patch = {"contributions": contributions}

    next_status = _advance_to_needs_summaries(
        conn,
        user_id,
        upload_id,
        upload,
        state=state,
        contributions_patch=contributions,
    )


    new_state = patch_upload_state(conn, upload_id, patch=patch, status=next_status)
    return {
        "upload_id": upload["upload_id"],
        "status": next_status,
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def set_project_supporting_csv_files(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    relpaths: list[str],
) -> dict:
    upload = _require_upload(conn, user_id, upload_id)
    _require_status(upload)

    state = upload.get("state") or {}

    files_payload = list_project_files(conn, user_id, upload_id, project_name)
    allowed = _allowed_csv_relpaths(files_payload)

    selected = _normalize_relpaths(relpaths)
    invalid = sorted([p for p in selected if p not in allowed])
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "One or more relpaths are not valid CSV files for this project",
                "invalid_relpaths": invalid,
            },
        )

    contributions = dict(state.get("contributions") or {})
    proj = dict(contributions.get(project_name) or {})
    proj["supporting_csv_relpaths"] = sorted(selected)
    contributions[project_name] = proj

    patch = {"contributions": contributions}

    next_status = _advance_to_needs_summaries(
        conn,
        user_id,
        upload_id,
        upload,
        state=state,
        contributions_patch=contributions,
    )

    new_state = patch_upload_state(conn, upload_id, patch=patch, status=next_status)
    return {
        "upload_id": upload["upload_id"],
        "status": next_status,
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def _require_upload(conn: sqlite3.Connection, user_id: int, upload_id: int) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def _require_status(upload: dict) -> None:
    if upload.get("status") not in _ALLOWED_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Upload not ready for supporting file selection (status={upload.get('status')})",
        )


def _get_main_file_relpath(state: dict, project_name: str) -> str:
    file_roles = state.get("file_roles") or {}
    proj = file_roles.get(project_name) or {}
    main_file = proj.get("main_file")
    if not main_file:
        raise HTTPException(
            status_code=409,
            detail={"message": "Main file must be selected before choosing supporting text files", "project_name": project_name},
        )
    return main_file


def _normalize_relpaths(relpaths: Iterable[str]) -> set[str]:
    relpaths = relpaths or []
    out: set[str] = set()
    for p in relpaths:
        try:
            out.add(safe_relpath(p))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    return out


def _allowed_supporting_text_relpaths(files_payload: dict, main_file_relpath: str) -> set[str]:
    allowed: set[str] = set()
    for item in (files_payload.get("text_files") or []):
        rp = (item.get("relpath") or "").strip()
        if rp and rp != main_file_relpath:
            allowed.add(rp)
    return allowed


def _allowed_csv_relpaths(files_payload: dict) -> set[str]:
    allowed: set[str] = set()
    for item in (files_payload.get("csv_files") or []):
        rp = (item.get("relpath") or "").strip()
        if rp:
            allowed.add(rp)
    return allowed

def _project_type_for_upload(state: dict, project_name: str) -> str | None:
    """
    Prefer manual project type over auto type for this upload.
    Returns "code" | "text" | None
    """
    types_manual = state.get("project_types_manual") or {}
    t = types_manual.get(project_name)
    if isinstance(t, str) and t:
        return t

    types_auto = state.get("project_types_auto") or {}
    t = types_auto.get(project_name)
    if isinstance(t, str) and t:
        return t

    return None


def _supporting_requirements_for_project(
    *,
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
    main_file_relpath: str,
) -> tuple[bool, bool]:
    """
    Returns (needs_supporting_text_step, needs_supporting_csv_step)
    based on whether the project actually has candidates.
    """
    files_payload = list_project_files(conn, user_id, upload_id, project_name)

    allowed_text = _allowed_supporting_text_relpaths(files_payload, main_file_relpath)
    allowed_csv = _allowed_csv_relpaths(files_payload)

    needs_text = bool(allowed_text)   # only if there are supporting text candidates
    needs_csv = bool(allowed_csv)     # only if there are csv candidates
    return needs_text, needs_csv


def _advance_to_needs_summaries(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    upload: dict,
    *,
    state: dict,
    contributions_patch: dict,
) -> str:
    """
    If we're currently in needs_file_roles, and all collaborative TEXT projects
    have completed the required file-role steps, advance to needs_summaries.

    Rule:
    - If project has CSV candidates -> must complete CSV supporting selection step (key exists)
    - If project has supporting text candidates -> must complete text supporting selection step (key exists)
    - If no candidates for a step -> step not required
    """
    cur = upload.get("status")
    if cur != "needs_file_roles":
        return cur

    layout = state.get("layout") or {}
    classifications = state.get("classifications") or {}

    known_projects = set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])
    if not known_projects:
        return cur

    for pname in sorted(known_projects):
        if (classifications.get(pname) or "") != "collaborative":
            continue

        ptype = _project_type_for_upload(state, pname)
        if ptype != "text":
            continue

        # must have selected a main file
        file_roles = (state.get("file_roles") or {}).get(pname) or {}
        main_file = file_roles.get("main_file")
        if not main_file:
            return cur

        proj_contrib = (contributions_patch or {}).get(pname) or {}

        # must have completed section selection step (key exists; list can be empty)
        if "main_section_ids" not in proj_contrib:
            return cur

        needs_text, needs_csv = _supporting_requirements_for_project(
            conn=conn,
            user_id=user_id,
            upload_id=upload_id,
            project_name=pname,
            main_file_relpath=main_file,
        )

        if needs_text and ("supporting_text_relpaths" not in proj_contrib):
            return cur

        if needs_csv and ("supporting_csv_relpaths" not in proj_contrib):
            return cur

    return "needs_summaries"