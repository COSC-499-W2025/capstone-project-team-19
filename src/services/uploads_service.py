from __future__ import annotations

from pathlib import Path
from fastapi import UploadFile, HTTPException
import shutil
import sqlite3
from typing import Any, Dict, List

from src.db.uploads import (
    create_upload,
    update_upload_zip_metadata,
    set_upload_state,
    get_upload_by_id,
    patch_upload_state,
)

from src.utils.parsing import ZIP_DATA_DIR, parse_zip_file, analyze_project_layout
from src.db.projects import record_project_classifications, store_parsed_files
from src.project_analysis import detect_project_type_auto

from src.services.uploads_utils import (
    safe_zip_filename,
    get_layout_known_projects,
    validate_classification_values,
    unknown_assignment_keys,
    validate_project_type_values,
    safe_relpath,
    build_file_item_from_row,
    categorize_project_files,
)


UPLOAD_DIR = Path(ZIP_DATA_DIR) / "_uploads"


def start_upload(conn: sqlite3.Connection, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = safe_zip_filename(file.filename or f"upload_{upload_id}.zip")
    zip_path = UPLOAD_DIR / f"{upload_id}_{zip_name}"

    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    update_upload_zip_metadata(conn, upload_id, zip_name=zip_name, zip_path=str(zip_path))

    files_info = parse_zip_file(str(zip_path), user_id=user_id, conn=conn)
    if not files_info:
        set_upload_state(
            conn,
            upload_id,
            state={"error": "No valid files were processed from ZIP."},
            status="failed",
        )
        return {
            "upload_id": upload_id,
            "status": "failed",
            "zip_name": zip_name,
            "state": {"error": "No valid files were processed from ZIP."},
        }

    store_parsed_files(conn, files_info, user_id)
    layout = analyze_project_layout(files_info)

    state = {
        "zip_name": zip_name,
        "zip_path": str(zip_path),
        "layout": layout,
        "files_info_count": len(files_info),
    }

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    # If everything was auto-classified, commit it immediately and move forward
    if auto_assignments and not pending_projects:
        record_project_classifications(conn, user_id, str(zip_path), zip_name, auto_assignments)

        type_result = detect_project_type_auto(conn, user_id, auto_assignments)

        patch = {
            **state,
            "classifications": auto_assignments,
            "project_types_auto": type_result["auto_types"],
            "project_types_mixed": type_result["mixed_projects"],
            "project_types_unknown": type_result["unknown_projects"],
        }

        next_status = "needs_project_types" if type_result["mixed_projects"] else "needs_file_roles"
        set_upload_state(conn, upload_id, state=patch, status=next_status)

        return {
            "upload_id": upload_id,
            "status": next_status,
            "zip_name": zip_name,
            "state": patch,
        }

    set_upload_state(conn, upload_id, state=state, status="needs_classification")
    return {
        "upload_id": upload_id,
        "status": "needs_classification",
        "zip_name": zip_name,
        "state": state,
    }


def get_upload_status(conn: sqlite3.Connection, user_id: int, upload_id: int) -> dict | None:
    row = get_upload_by_id(conn, upload_id)
    if not row or row["user_id"] != user_id:
        return None

    return {
        "upload_id": row["upload_id"],
        "status": row["status"],
        "zip_name": row.get("zip_name"),
        "state": row.get("state") or {},
    }


def submit_classifications(conn: sqlite3.Connection, user_id: int, upload_id: int, assignments: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] not in {"needs_classification", "parsed"}:
        raise HTTPException(status_code=409, detail=f"Upload not ready for classifications (status={upload['status']})")

    if not assignments:
        raise HTTPException(status_code=422, detail="assignments cannot be empty")

    invalid_vals = validate_classification_values(assignments)
    if invalid_vals:
        raise HTTPException(status_code=422, detail={"invalid_assignments": invalid_vals})

    state = upload.get("state") or {}
    known_projects = get_layout_known_projects(state)
    if not known_projects:
        raise HTTPException(status_code=409, detail="Upload layout missing; parse step not completed")

    unknown = unknown_assignment_keys(assignments, known_projects)
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_projects": unknown, "known_projects": sorted(known_projects)})

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    zip_name = upload.get("zip_name") or Path(zip_path).stem

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)

    type_result = detect_project_type_auto(conn, user_id, assignments)

    patch = {
        "classifications": assignments,
        "project_types_auto": type_result["auto_types"],
        "project_types_mixed": type_result["mixed_projects"],
        "project_types_unknown": type_result["unknown_projects"],
    }

    next_status = "needs_project_types" if type_result["mixed_projects"] else "needs_file_roles"

    new_state = patch_upload_state(conn, upload_id, patch=patch, status=next_status)

    return {
        "upload_id": upload_id,
        "status": next_status,
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def submit_project_types(conn: sqlite3.Connection, user_id: int, upload_id: int, project_types: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    state = upload.get("state") or {}
    mixed = set(state.get("project_types_mixed") or [])
    if not mixed:
        raise HTTPException(status_code=409, detail="No mixed projects require type selection")

    bad_vals = validate_project_type_values(project_types)
    if bad_vals:
        raise HTTPException(status_code=422, detail={"invalid_project_types": bad_vals})

    extra = set(project_types.keys()) - mixed
    missing = mixed - set(project_types.keys())
    if extra:
        raise HTTPException(status_code=422, detail={"unknown_projects": sorted(extra)})
    if missing:
        raise HTTPException(status_code=422, detail={"missing_projects": sorted(missing)})

    for project_name, ptype in project_types.items():
        conn.execute(
            """
            UPDATE project_classifications
            SET project_type = ?
            WHERE user_id = ? AND project_name = ?
            """,
            (ptype, user_id, project_name),
        )
    conn.commit()

    new_state = patch_upload_state(
        conn,
        upload_id,
        patch={"project_types_manual": project_types},
        status="needs_file_roles",
    )

    return {
        "upload_id": upload_id,
        "status": "needs_file_roles",
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }