from __future__ import annotations

from pathlib import Path
from fastapi import UploadFile, HTTPException
import shutil
import sqlite3

from src.db.uploads import (
    create_upload,
    update_upload_zip_metadata,
    set_upload_state,
    get_upload_by_id,
    patch_upload_state,
)

from src.utils.parsing import ZIP_DATA_DIR, parse_zip_file, analyze_project_layout
from src.db.projects import record_project_classifications, store_parsed_files

from src.utils.deduplication.api_integration import (
    run_deduplication_for_projects_api,
    find_project_dir,
    force_register_new_project,
    force_register_new_version,
)

from src.services.uploads_util import (
    extract_dir_from_upload_zip,
    rename_project_in_layout,
    remove_project_from_layout,
    apply_project_rename_to_files_info,
    build_project_filetype_index,
    infer_project_types_from_index,
    rename_project_key_in_index,
    remove_project_key_in_index,
)

from src.services.uploads_file_roles_util import (
    safe_relpath,
    build_file_item_from_row,
    categorize_project_files,
)

UPLOAD_DIR = Path(ZIP_DATA_DIR) / "_uploads"

# defaults if dedup logic is not executed or returns nothing
skipped_set: set[str] = set()
asks: dict = {}
new_versions: dict = {}
project_filetype_index: dict = {}


def start_upload(conn: sqlite3.Connection, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = file.filename
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

    layout = analyze_project_layout(files_info)
    
    extract_dir = extract_dir_from_upload_zip(ZIP_DATA_DIR, str(zip_path))

    dedup = run_deduplication_for_projects_api(conn, user_id, str(extract_dir), layout, upload_id=upload_id)

    skipped_set = set(dedup.get("skipped") or set())
    asks: dict = dedup.get("asks") or {}
    new_versions: dict = dedup.get("new_versions") or {}

    # 1) Apply auto-skip BEFORE writing parsed files to DB
    if skipped_set:
        files_info = [f for f in files_info if f.get("project_name") not in skipped_set]
        layout = analyze_project_layout(files_info)

    # 2) Apply auto-rename for 'new_version' suggestions
    for old_name, existing_name in new_versions.items():
        if existing_name and old_name != existing_name:
            apply_project_rename_to_files_info(files_info, old_name, existing_name)
            layout = rename_project_in_layout(layout, old_name, existing_name)

    # If everything got removed, fail early
    if not files_info:
        state = {
            "zip_name": zip_name,
            "zip_path": str(zip_path),
            "layout": layout,
            "files_info_count": 0,
            "dedup_skipped_projects": sorted(list(skipped_set)),
            "dedup_asks": asks,
            "dedup_new_versions": new_versions,
            "project_filetype_index": {},
            "message": "All projects were skipped by deduplication (duplicates).",
        }
        set_upload_state(conn, upload_id, state=state, status="failed")
        return {"upload_id": upload_id, "status": "failed", "zip_name": zip_name, "state": state}

    # Store parsed files (kept + post-rename only)
    store_parsed_files(conn, files_info, user_id)

    # IMPORTANT: build upload-scoped filetype index from CURRENT upload files_info
    project_filetype_index = build_project_filetype_index(files_info)

    state = {
        "zip_name": zip_name,
        "zip_path": str(zip_path),
        "layout": layout,
        "files_info_count": len(files_info),
        "dedup_skipped_projects": sorted(list(skipped_set)),
        "dedup_asks": asks,
        "dedup_new_versions": new_versions,
        "project_filetype_index": project_filetype_index,
    }

    # If unresolved asks exist, stop before classification (matches CLI ordering)
    if asks:
        set_upload_state(conn, upload_id, state=state, status="needs_dedup")
        return {"upload_id": upload_id, "status": "needs_dedup", "zip_name": zip_name, "state": state}

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    # If everything is auto-classified, commit and infer project types (upload-scoped)
    if auto_assignments and not pending_projects:
        record_project_classifications(conn, user_id, str(zip_path), zip_name, auto_assignments)

        projects = set(auto_assignments.keys())
        type_result = infer_project_types_from_index(projects, project_filetype_index)

        patch = {
            **state,
            "classifications": auto_assignments,
            "project_types_auto": type_result["auto_types"],
            "project_types_mixed": type_result["mixed_projects"],
            "project_types_unknown": type_result["unknown_projects"],
        }

        needs_type_choice = bool(type_result["mixed_projects"] or type_result["unknown_projects"])
        next_status = "needs_project_types" if needs_type_choice else "needs_file_roles"

        set_upload_state(conn, upload_id, state=patch, status=next_status)
        return {"upload_id": upload_id, "status": next_status, "zip_name": zip_name, "state": patch}

    set_upload_state(conn, upload_id, state=state, status="needs_classification")
    return {"upload_id": upload_id, "status": "needs_classification", "zip_name": zip_name, "state": state}


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


def resolve_dedup(conn: sqlite3.Connection, user_id: int, upload_id: int, decisions: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] != "needs_dedup":
        raise HTTPException(status_code=409, detail=f"Upload not ready for dedup resolve (status={upload['status']})")

    state = upload.get("state") or {}
    layout = state.get("layout") or {}
    asks: dict = state.get("dedup_asks") or {}
    index: dict = state.get("project_filetype_index") or {}

    if not asks:
        raise HTTPException(status_code=409, detail="No dedup ask cases to resolve")

    if not decisions:
        raise HTTPException(status_code=422, detail="decisions cannot be empty")

    allowed = {"skip", "new_project", "new_version"}
    bad = {k: v for k, v in decisions.items() if v not in allowed}
    if bad:
        raise HTTPException(status_code=422, detail={"invalid_decisions": bad})

    ask_keys = set(asks.keys())
    decision_keys = set(decisions.keys())

    extra = sorted(list(decision_keys - ask_keys))
    missing = sorted(list(ask_keys - decision_keys))
    if extra:
        raise HTTPException(status_code=422, detail={"unknown_projects": extra})
    if missing:
        raise HTTPException(status_code=422, detail={"missing_projects": missing})

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")
    zip_name = upload.get("zip_name") or Path(zip_path).stem

    extract_dir = extract_dir_from_upload_zip(ZIP_DATA_DIR, zip_path)
    root_name = layout.get("root_name")

    skipped_now: set[str] = set()
    renames: dict[str, str] = {}

    for project_name, decision in decisions.items():
        ask_item = asks.get(project_name) or {}
        project_dir = find_project_dir(str(extract_dir), root_name, project_name)
        if not project_dir:
            raise HTTPException(status_code=404, detail=f"Project directory not found for '{project_name}'")

        if decision == "skip":
            skipped_now.add(project_name)
            remove_project_from_layout(layout, project_name)
            remove_project_key_in_index(index, project_name)

            # remove this project's stored parsed files so later steps don't see it
            conn.execute(
                "DELETE FROM files WHERE user_id = ? AND project_name = ?",
                (user_id, project_name),
            )
            conn.commit()
            continue

        if decision == "new_project":
            force_register_new_project(conn, user_id, project_name, project_dir, upload_id=upload_id)
            continue

        if decision == "new_version":
            best_pk = ask_item.get("best_match_project_key")
            existing = ask_item.get("existing")
            if best_pk is None or not existing:
                raise HTTPException(status_code=409, detail=f"Missing best-match info for '{project_name}'")

            force_register_new_version(conn, int(best_pk), project_dir, upload_id=upload_id)

            if project_name != existing:
                conn.execute(
                    "UPDATE files SET project_name = ? WHERE user_id = ? AND project_name = ?",
                    (existing, user_id, project_name),
                )
                conn.commit()

                rename_project_in_layout(layout, project_name, existing)
                rename_project_key_in_index(index, project_name, existing)

                renames[project_name] = existing

    prev_skipped = set(state.get("dedup_skipped_projects") or [])
    merged_skipped = sorted(list(prev_skipped | skipped_now))

    state_patch = {
        "layout": layout,
        "dedup_skipped_projects": merged_skipped,
        "dedup_asks": {},  # resolved
        "dedup_resolved": decisions,
        "dedup_renames": renames,
        "project_filetype_index": index,
    }

    remaining_projects = set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])
    if not remaining_projects:
        new_state = patch_upload_state(conn, upload_id, patch=state_patch, status="failed")
        return {"upload_id": upload_id, "status": "failed", "zip_name": zip_name, "state": new_state}

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    if auto_assignments and not pending_projects:
        record_project_classifications(conn, user_id, zip_path, zip_name, auto_assignments)

        projects = set(auto_assignments.keys())
        type_result = infer_project_types_from_index(projects, index)

        state_patch.update(
            {
                "classifications": auto_assignments,
                "project_types_auto": type_result["auto_types"],
                "project_types_mixed": type_result["mixed_projects"],
                "project_types_unknown": type_result["unknown_projects"],
            }
        )

        needs_type_choice = bool(type_result["mixed_projects"] or type_result["unknown_projects"])
        next_status = "needs_project_types" if needs_type_choice else "needs_file_roles"

        new_state = patch_upload_state(conn, upload_id, patch=state_patch, status=next_status)
        return {"upload_id": upload_id, "status": next_status, "zip_name": zip_name, "state": new_state}

    new_state = patch_upload_state(conn, upload_id, patch=state_patch, status="needs_classification")
    return {"upload_id": upload_id, "status": "needs_classification", "zip_name": zip_name, "state": new_state}


def submit_classifications(conn: sqlite3.Connection, user_id: int, upload_id: int, assignments: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] not in {"needs_classification", "parsed"}:
        raise HTTPException(status_code=409, detail=f"Upload not ready for classifications (status={upload['status']})")

    if not assignments:
        raise HTTPException(status_code=422, detail="assignments cannot be empty")

    allowed = {"individual", "collaborative"}
    invalid = {k: v for k, v in assignments.items() if v not in allowed}
    if invalid:
        raise HTTPException(status_code=422, detail={"invalid_assignments": invalid})

    state = upload.get("state") or {}
    layout = state.get("layout") or {}
    index: dict = state.get("project_filetype_index") or {}

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
    zip_name = upload.get("zip_name") or Path(zip_path).stem

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)

    projects = set(assignments.keys())
    type_result = infer_project_types_from_index(projects, index)

    patch = {
        "classifications": assignments,
        "project_types_auto": type_result["auto_types"],
        "project_types_mixed": type_result["mixed_projects"],
        "project_types_unknown": type_result["unknown_projects"],
    }

    needs_type_choice = bool(type_result["mixed_projects"] or type_result["unknown_projects"])
    next_status = "needs_project_types" if needs_type_choice else "needs_file_roles"

    new_state = patch_upload_state(conn, upload_id, patch=patch, status=next_status)
    return {"upload_id": upload_id, "status": next_status, "zip_name": upload.get("zip_name"), "state": new_state}


def submit_project_types(conn: sqlite3.Connection, user_id: int, upload_id: int, project_types: dict[str, str]) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    state = upload.get("state") or {}
    mixed = set(state.get("project_types_mixed") or [])
    unknown = set(state.get("project_types_unknown") or [])

    # user is choosing types for mixed/unknown
    needs_choice = mixed | unknown
    if not needs_choice:
        raise HTTPException(status_code=409, detail="No projects require type selection")

    allowed = {"code", "text"}
    bad_vals = {k: v for k, v in project_types.items() if v not in allowed}
    if bad_vals:
        raise HTTPException(status_code=422, detail={"invalid_project_types": bad_vals})

    extra = set(project_types.keys()) - needs_choice
    missing = needs_choice - set(project_types.keys())
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
    return {"upload_id": upload_id, "status": "needs_file_roles", "zip_name": upload.get("zip_name"), "state": new_state}


def _known_projects_from_layout(layout: dict) -> set[str]:
    return set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])


def _rows_for_project_scoped_to_upload(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    zip_path: str,
):
    """
    Try to scope file listing to the current upload by matching the zip stem in file_path.
    Falls back to unscoped query if the scoped one returns nothing (to avoid breaking if
    file_path storage is inconsistent).
    """
    zip_stem = Path(zip_path).stem

    scoped = conn.execute(
        """
        SELECT file_name, file_path, extension, file_type, size_bytes, created, modified, project_name
        FROM files
        WHERE user_id = ? AND project_name = ?
          AND (
            file_path LIKE ? OR file_path LIKE ?
          )
        ORDER BY file_path ASC
        """,
        (user_id, project_name, f"%/{zip_stem}/%", f"{zip_stem}/%"),
    ).fetchall()

    if scoped:
        return scoped

    # fallback (older DB rows might not include zip_stem)
    return conn.execute(
        """
        SELECT file_name, file_path, extension, file_type, size_bytes, created, modified, project_name
        FROM files
        WHERE user_id = ? AND project_name = ?
        ORDER BY file_path ASC
        """,
        (user_id, project_name),
    ).fetchall()


def list_project_files(conn: sqlite3.Connection, user_id: int, upload_id: int, project_name: str) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] not in {"needs_file_roles", "needs_summaries"}:
        raise HTTPException(status_code=409, detail=f"Upload not ready for file picking (status={upload['status']})")

    state = upload.get("state") or {}
    layout = state.get("layout") or {}
    known_projects = _known_projects_from_layout(layout)
    if project_name not in known_projects:
        raise HTTPException(status_code=404, detail="Project not found in this upload")

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    rows = _rows_for_project_scoped_to_upload(conn, user_id, project_name, zip_path)

    items = [build_file_item_from_row(Path(ZIP_DATA_DIR), r) for r in rows]
    buckets = categorize_project_files(items)

    return {
        "upload_id": upload_id,
        "project_name": project_name,
        **buckets,
    }


def set_project_main_file(conn: sqlite3.Connection, user_id: int, upload_id: int, project_name: str, relpath: str) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] != "needs_file_roles":
        raise HTTPException(status_code=409, detail=f"Upload not ready to set main file (status={upload['status']})")

    state = upload.get("state") or {}
    layout = state.get("layout") or {}
    known_projects = _known_projects_from_layout(layout)
    if project_name not in known_projects:
        raise HTTPException(status_code=404, detail="Project not found in this upload")

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    try:
        relpath_norm = safe_relpath(relpath)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rows = _rows_for_project_scoped_to_upload(conn, user_id, project_name, zip_path)
    valid_relpaths = {
        build_file_item_from_row(Path(ZIP_DATA_DIR), r).get("relpath") for r in rows
    }

    if relpath_norm not in valid_relpaths:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "relpath not found for this project",
                "project_name": project_name,
                "relpath": relpath_norm,
            },
        )

    patch = {
        "file_roles": {
            **(state.get("file_roles") or {}),
            project_name: {
                **((state.get("file_roles") or {}).get(project_name) or {}),
                "main_file": relpath_norm,
            },
        }
    }

    new_state = patch_upload_state(conn, upload_id, patch=patch, status="needs_file_roles")

    return {
        "upload_id": upload_id,
        "status": upload["status"],
        "zip_name": upload.get("zip_name"),
        "state": new_state,
    }
