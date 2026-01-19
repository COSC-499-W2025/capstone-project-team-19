from pathlib import Path
from fastapi import UploadFile, HTTPException
import re
import shutil

from src.db.uploads import (
    create_upload,
    update_upload_zip_metadata,
    set_upload_state,
    get_upload_by_id,
    patch_upload_state,
    update_upload_status
)

from src.utils.parsing import ZIP_DATA_DIR, parse_zip_file, analyze_project_layout
from src.db.projects import record_project_classifications, store_parsed_files
from src.project_analysis import detect_project_type_auto

UPLOAD_DIR = Path(ZIP_DATA_DIR) / "_uploads"


def _safe_name(name: str) -> str:
    name = (name or "").strip()
    name = name.split("/")[-1].split("\\")[-1]
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "upload.zip"


def start_upload(conn, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = _safe_name(file.filename or f"upload_{upload_id}.zip")
    zip_path = UPLOAD_DIR / f"{upload_id}_{zip_name}"

    # stream copy (don’t read entire zip into memory)
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    update_upload_zip_metadata(conn, upload_id, zip_name=zip_name, zip_path=str(zip_path))

    # Step 4A: parse + layout (same automatic work CLI does)
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

    # if everything was auto-classified, commit it immediately and move forward
    if auto_assignments and not pending_projects:
        # persist to same table CLI uses
        record_project_classifications(conn, user_id, str(zip_path), zip_name, auto_assignments)

        # auto-detect project types (API-safe)
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


def get_upload_status(conn, user_id: int, upload_id: int) -> dict | None:
    row = get_upload_by_id(conn, upload_id)
    if not row or row["user_id"] != user_id:
        return None

    return {
        "upload_id": row["upload_id"],
        "status": row["status"],
        "zip_name": row.get("zip_name"),
        "state": row.get("state") or {},
    }


def submit_classifications(conn, user_id: int, upload_id: int, assignments: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] not in {"needs_classification", "parsed"}:
        raise HTTPException(
            status_code=409,
            detail=f"Upload not ready for classifications (status={upload['status']})",
        )

    if not assignments:
        raise HTTPException(status_code=422, detail="assignments cannot be empty")

    allowed = {"individual", "collaborative"}
    invalid = {k: v for k, v in assignments.items() if v not in allowed}
    if invalid:
        raise HTTPException(status_code=422, detail={"invalid_assignments": invalid})
    
    state = upload.get("state") or {}
    layout = state.get("layout") or {}

    known_projects = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
    if not known_projects:
        raise HTTPException(status_code=409, detail="Upload layout missing; parse step not completed")

    unknown_projects = [p for p in assignments.keys() if p not in known_projects]
    if unknown_projects:
        raise HTTPException(
            status_code=422,
            detail={"unknown_projects": unknown_projects, "known_projects": sorted(known_projects)},
        )

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")
    
    zip_name = upload.get("zip_name")
    if not zip_name:
        zip_name = Path(zip_path).stem

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)
    
    # auto-detect project types (API-safe)
    type_result = detect_project_type_auto(conn, user_id, assignments)
    
    patch = {
        "classifications": assignments,
        "project_types_auto": type_result["auto_types"],
        "project_types_mixed": type_result["mixed_projects"],
        "project_types_unknown": type_result["unknown_projects"],
    }
    
    # if any mixed → next step is project-types
    next_status = "needs_project_types" if type_result["mixed_projects"] else "needs_file_roles"

    new_state = patch_upload_state(
        conn,
        upload_id,
        patch=patch,
        status=next_status,
    )

    return {
        "upload_id": upload_id,
        "status": next_status,
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def submit_project_types(conn, user_id: int, upload_id: int, project_types: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    state = upload.get("state") or {}
    mixed = set(state.get("project_types_mixed") or [])

    if not mixed:
        raise HTTPException(status_code=409, detail="No mixed projects require type selection")

    allowed = {"code", "text"}
    bad_vals = {k: v for k, v in project_types.items() if v not in allowed}
    if bad_vals:
        raise HTTPException(status_code=422, detail={"invalid_project_types": bad_vals})

    # must cover only mixed projects (no extras)
    extra = set(project_types.keys()) - mixed
    missing = mixed - set(project_types.keys())
    if extra:
        raise HTTPException(status_code=422, detail={"unknown_projects": sorted(extra)})
    if missing:
        raise HTTPException(status_code=422, detail={"missing_projects": sorted(missing)})

    for project_name, ptype in project_types.items():
        conn.execute("""
            UPDATE project_classifications
            SET project_type = ?
            WHERE user_id = ? AND project_name = ?
        """, (ptype, user_id, project_name))
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

