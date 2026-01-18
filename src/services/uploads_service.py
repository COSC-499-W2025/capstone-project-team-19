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

    # optional: persist parsed metadata to DB (matches your CLI behavior if you already do this there)
    store_parsed_files(conn, files_info, user_id)

    layout = analyze_project_layout(files_info)

    state = {
        "zip_name": zip_name,
        "zip_path": str(zip_path),
        "layout": layout,
        "files_info_count": len(files_info),
    }

    # after parsing, next step is usually classification
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

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    zip_name = Path(zip_path).stem

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)

    new_state = patch_upload_state(
        conn,
        upload_id,
        patch={"classifications": assignments},
        status="parsed",
    )

    return {
        "upload_id": upload_id,
        "status": "parsed",
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }


def submit_project_types(conn, user_id: int, upload_id: int, project_types: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    state = upload.get("state") or {}
    layout = state.get("layout") or {}

    # We need to know what projects exist from layout
    known_projects = set(layout.get("auto_assignments", {}).keys()) | set(layout.get("pending_projects", []))

    if not known_projects:
        raise HTTPException(status_code=409, detail="Upload has no detected projects to set types for")

    # Validate keys are known projects
    unknown = {k: v for k, v in project_types.items() if k not in known_projects}
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_projects": list(unknown.keys())})

    # Validate values
    allowed_types = {"code", "text"}
    bad_vals = {k: v for k, v in project_types.items() if v not in allowed_types}
    if bad_vals:
        raise HTTPException(status_code=422, detail={"invalid_project_types": bad_vals})

    new_state = patch_upload_state(
        conn,
        upload_id,
        patch={"project_types": project_types},
        status=upload["status"], 
    )

    update_upload_status(conn, upload_id, "needs_file_roles")

    refreshed = get_upload_by_id(conn, upload_id)
    return {
        "upload_id": upload_id,
        "status": refreshed["status"],
        "zip_name": refreshed.get("zip_name"),
        "state": refreshed.get("state") or {},
    }
