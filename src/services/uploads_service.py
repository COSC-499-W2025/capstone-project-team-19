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
from src.project_analysis import detect_project_type_auto

from src.utils.deduplication.api_integration import (
    run_deduplication_for_projects_api,
    find_project_dir,
    force_register_new_project,
    force_register_new_version,
)

from src.services.uploads_util import (
    safe_upload_zip_name,
    extract_dir_from_upload_zip,
    rename_project_in_layout,
    remove_project_from_layout,
    apply_project_rename_to_files_info,
)

from src.services.uploads_validation import (
    require_upload_owned,
    require_upload_status,
    require_non_empty_dict,
    require_layout_present,
    validate_classification_values,
    validate_classification_keys_against_layout,
    validate_project_types_payload,
    validate_dedup_decisions,
)

from src.services.uploads_state import (
    upload_response,
    build_failed_parse_state,
    build_all_skipped_state,
    build_base_state,
    add_type_detection_patch,
    next_status_from_type_result,
)

UPLOAD_DIR = Path(ZIP_DATA_DIR) / "_uploads"


def start_upload(conn: sqlite3.Connection, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = safe_upload_zip_name(file.filename or f"upload_{upload_id}.zip")
    zip_path = UPLOAD_DIR / f"{upload_id}_{zip_name}"

    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    update_upload_zip_metadata(conn, upload_id, zip_name=zip_name, zip_path=str(zip_path))

    files_info = parse_zip_file(str(zip_path), user_id=user_id, conn=conn)
    if not files_info:
        state = build_failed_parse_state(zip_name, str(zip_path))
        set_upload_state(conn, upload_id, state=state, status="failed")
        return upload_response(upload_id, "failed", zip_name, state)

    layout = analyze_project_layout(files_info)
    extract_dir = extract_dir_from_upload_zip(ZIP_DATA_DIR, str(zip_path))

    dedup = run_deduplication_for_projects_api(conn, user_id, str(extract_dir), layout)
    skipped_set = set(dedup.get("skipped") or set())
    asks = dedup.get("asks") or {}
    new_versions = dedup.get("new_versions") or {}

    if skipped_set:
        files_info = [f for f in files_info if f.get("project_name") not in skipped_set]
        layout = analyze_project_layout(files_info)

    for old_name, existing_name in new_versions.items():
        if existing_name and old_name != existing_name:
            apply_project_rename_to_files_info(files_info, old_name, existing_name)
            layout = rename_project_in_layout(layout, old_name, existing_name)

    if not files_info:
        state = build_all_skipped_state(zip_name, str(zip_path), layout, skipped_set, asks, new_versions)
        set_upload_state(conn, upload_id, state=state, status="failed")
        return upload_response(upload_id, "failed", zip_name, state)

    store_parsed_files(conn, files_info, user_id)

    state = build_base_state(
        zip_name=zip_name,
        zip_path=str(zip_path),
        layout=layout,
        files_info_count=len(files_info),
        skipped=skipped_set,
        asks=asks,
        new_versions=new_versions,
    )

    if asks:
        set_upload_state(conn, upload_id, state=state, status="needs_dedup")
        return upload_response(upload_id, "needs_dedup", zip_name, state)

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    if auto_assignments and not pending_projects:
        record_project_classifications(conn, user_id, str(zip_path), zip_name, auto_assignments)

        type_result = detect_project_type_auto(conn, user_id, auto_assignments)
        patch = add_type_detection_patch(state, auto_assignments, type_result)
        next_status = next_status_from_type_result(type_result)

        set_upload_state(conn, upload_id, state=patch, status=next_status)
        return upload_response(upload_id, next_status, zip_name, patch)

    set_upload_state(conn, upload_id, state=state, status="needs_classification")
    return upload_response(upload_id, "needs_classification", zip_name, state)


def get_upload_status(conn: sqlite3.Connection, user_id: int, upload_id: int) -> dict | None:
    row = get_upload_by_id(conn, upload_id)
    if not row or row["user_id"] != user_id:
        return None

    return upload_response(
        upload_id=row["upload_id"],
        status=row["status"],
        zip_name=row.get("zip_name"),
        state=row.get("state") or {},
    )


def resolve_dedup(conn: sqlite3.Connection, user_id: int, upload_id: int, decisions: dict[str, str]) -> dict:
    upload = require_upload_owned(get_upload_by_id(conn, upload_id), user_id)
    require_upload_status(upload, {"needs_dedup"}, "dedup resolve")
    require_non_empty_dict(decisions, "decisions")

    state = upload.get("state") or {}
    layout = (state.get("layout") or {})
    asks: dict = state.get("dedup_asks") or {}

    if not asks:
        raise HTTPException(status_code=409, detail="No dedup ask cases to resolve")

    validate_dedup_decisions(asks, decisions)

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
            layout = remove_project_from_layout(layout, project_name)

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
            if not best_pk or not existing:
                raise HTTPException(status_code=409, detail=f"Missing best-match info for '{project_name}'")

            force_register_new_version(conn, int(best_pk), project_dir, upload_id=upload_id)

            if project_name != existing:
                conn.execute(
                    "UPDATE files SET project_name = ? WHERE user_id = ? AND project_name = ?",
                    (existing, user_id, project_name),
                )
                conn.commit()

                layout = rename_project_in_layout(layout, project_name, existing)
                renames[project_name] = existing

    prev_skipped = set(state.get("dedup_skipped_projects") or [])
    merged_skipped = sorted(list(prev_skipped | skipped_now))

    state_patch = {
        "layout": layout,
        "dedup_skipped_projects": merged_skipped,
        "dedup_asks": {},
        "dedup_resolved": decisions,
        "dedup_renames": renames,
    }

    remaining_projects = set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])
    if not remaining_projects:
        new_state = patch_upload_state(conn, upload_id, patch=state_patch, status="failed")
        return upload_response(upload_id, "failed", zip_name, new_state)

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    if auto_assignments and not pending_projects:
        record_project_classifications(conn, user_id, zip_path, zip_name, auto_assignments)

        type_result = detect_project_type_auto(conn, user_id, auto_assignments)
        state_patch = add_type_detection_patch(state_patch, auto_assignments, type_result)

        next_status = next_status_from_type_result(type_result)
        new_state = patch_upload_state(conn, upload_id, patch=state_patch, status=next_status)
        return upload_response(upload_id, next_status, zip_name, new_state)

    new_state = patch_upload_state(conn, upload_id, patch=state_patch, status="needs_classification")
    return upload_response(upload_id, "needs_classification", zip_name, new_state)


def submit_classifications(conn: sqlite3.Connection, user_id: int, upload_id: int, assignments: dict[str, str]) -> dict:
    upload = require_upload_owned(get_upload_by_id(conn, upload_id), user_id)
    require_upload_status(upload, {"needs_classification", "parsed"}, "classifications")
    require_non_empty_dict(assignments, "assignments")

    validate_classification_values(assignments)

    state = upload.get("state") or {}
    layout = require_layout_present(state)
    validate_classification_keys_against_layout(layout, assignments)

    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")
    zip_name = upload.get("zip_name") or Path(zip_path).stem

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)

    type_result = detect_project_type_auto(conn, user_id, assignments)
    patch = add_type_detection_patch({}, assignments, type_result)

    next_status = next_status_from_type_result(type_result)
    new_state = patch_upload_state(conn, upload_id, patch=patch, status=next_status)

    return upload_response(upload_id, next_status, upload.get("zip_name"), new_state)


def submit_project_types(conn: sqlite3.Connection, user_id: int, upload_id: int, project_types: dict[str, str]) -> dict:
    upload = require_upload_owned(get_upload_by_id(conn, upload_id), user_id)

    state = upload.get("state") or {}
    mixed = set(state.get("project_types_mixed") or [])
    if not mixed:
        raise HTTPException(status_code=409, detail="No mixed projects require type selection")

    validate_project_types_payload(mixed, project_types)

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

    return upload_response(upload_id, "needs_file_roles", upload.get("zip_name"), new_state)
