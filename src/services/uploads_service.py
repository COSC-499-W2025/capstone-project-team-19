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
from src.db.projects import (
    store_parsed_files,
    update_project_metadata,
    get_project_key,
)

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


def start_upload(conn: sqlite3.Connection, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = file.filename
    zip_path = UPLOAD_DIR / f"{upload_id}_{zip_name}"

    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    update_upload_zip_metadata(conn, upload_id, zip_name=zip_name, zip_path=str(zip_path))

    # Parse/extract ZIP, but do NOT persist files yet: we want to attach version_key after dedup.
    files_info = parse_zip_file(str(zip_path), user_id=user_id, conn=conn, persist_to_db=False)
    if not files_info:
        set_upload_state(conn, upload_id, state={"error": "No valid files were processed from ZIP."}, status="failed")
        return {"upload_id": upload_id, "status": "failed", "zip_name": zip_name, "state": {"error": "No valid files were processed from ZIP."}}

    layout = analyze_project_layout(files_info)

    # Dedup + version registration (creates `projects` + `project_versions` rows)
    extract_dir = extract_dir_from_upload_zip(ZIP_DATA_DIR, str(zip_path))
    dedup = run_deduplication_for_projects_api(
        conn,
        user_id,
        target_dir=str(extract_dir),
        layout=layout,
        upload_id=upload_id,
    )

    skipped_set: set[str] = set(dedup.get("skipped") or set())
    asks: dict = dedup.get("asks") or {}
    new_versions: dict = dedup.get("new_versions") or {}
    decisions: dict = dedup.get("decisions") or {}
    # Collect any dedup warnings for clients/CLI to display.
    dedup_warnings: dict[str, str] = {}
    for pname, d in (decisions or {}).items():
        w = (d or {}).get("warning")
        if isinstance(w, str) and w.strip():
            dedup_warnings[pname] = w.strip()

    # Apply dedup renames to layout + files_info (so later steps operate on final project names)
    for old_name, existing_name in (new_versions or {}).items():
        if old_name and existing_name and old_name != existing_name:
            rename_project_in_layout(layout, old_name, existing_name)
            apply_project_rename_to_files_info(files_info, old_name, existing_name)

    # Remove skipped projects from layout + files_info
    if skipped_set:
        for name in sorted(skipped_set):
            remove_project_from_layout(layout, name)
        files_info = [f for f in files_info if f.get("project_name") not in skipped_set]

    # Attach version_key to parsed files (per final project name)
    version_keys: dict[str, int] = {}
    project_keys: dict[str, int] = {}
    for orig_name, d in (decisions or {}).items():
        kind = (d or {}).get("kind")
        if kind in {"new_project", "new_version"}:
            vk = d.get("version_key")
            pk = d.get("project_key")
            existing_name = d.get("existing_name")
            final_name = existing_name or orig_name
            if isinstance(vk, int) and final_name:
                version_keys[final_name] = vk
            if isinstance(pk, int) and final_name:
                project_keys[final_name] = pk

    for f in files_info:
        pname = f.get("project_name")
        if pname in version_keys:
            f["version_key"] = version_keys[pname]

    # Persist parsed files once (after dedup tagging)
    store_parsed_files(conn, files_info, user_id)

    # Persist extraction root for these versions (used by skills/text pipelines to locate files on disk)
    zip_root = Path(str(zip_path)).stem
    for vk in version_keys.values():
        if isinstance(vk, int):
            conn.execute(
                "UPDATE project_versions SET extraction_root = COALESCE(extraction_root, ?) WHERE version_key = ?",
                (zip_root, vk),
            )
    conn.commit()

    project_filetype_index: dict = build_project_filetype_index(files_info)

    state = {
        "zip_name": zip_name,
        "zip_path": str(zip_path),
        "layout": layout,
        "files_info_count": len(files_info),
        "dedup_skipped_projects": sorted(list(skipped_set)),
        "dedup_asks": asks,
        "dedup_new_versions": new_versions,
        "dedup_warnings": dedup_warnings,
        "dedup_version_keys": version_keys,
        "dedup_project_keys": project_keys,
        "project_filetype_index": project_filetype_index,
    }

    if asks:
        set_upload_state(conn, upload_id, state=state, status="needs_dedup")
        return {"upload_id": upload_id, "status": "needs_dedup", "zip_name": zip_name, "state": state}

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    # If everything is auto-classified, commit and infer project types (upload-scoped)
    if auto_assignments and not pending_projects:
        # Persist classification on canonical `projects` rows.
        for project_name, classification in auto_assignments.items():
            pk = project_keys.get(project_name)
            if isinstance(pk, int):
                update_project_metadata(conn, pk, classification=classification)

        projects = set(auto_assignments.keys())
        type_result = infer_project_types_from_index(projects, project_filetype_index)

        # Persist auto-detected types on `projects`
        for project_name, ptype in (type_result.get("auto_types") or {}).items():
            pk = project_keys.get(project_name)
            if isinstance(pk, int):
                update_project_metadata(conn, pk, project_type=ptype)

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
    # Key maps created during start_upload for auto-handled projects (new_project/new_version).
    # For 'ask' cases, these are missing until we resolve dedup and must be backfilled.
    dedup_version_keys: dict[str, int] = dict(state.get("dedup_version_keys") or {})
    dedup_project_keys: dict[str, int] = dict(state.get("dedup_project_keys") or {})

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
    zip_stem = Path(zip_path).stem
    zip_root = zip_stem  # used by analysis to locate extracted content on disk

    skipped_now: set[str] = set()
    renames: dict[str, str] = {}

    # Re-collect parsed file metadata for this upload so we can persist ask-cases
    # after creating their version_key. (Ask-cases have no version_key yet, so they
    # were intentionally not inserted into the versioned-only `files` table.)
    all_files_info = parse_zip_file(str(zip_path), user_id=user_id, conn=conn, persist_to_db=False) or []

    for project_name, decision in decisions.items():
        ask_item = asks.get(project_name) or {}
        project_dir = find_project_dir(str(extract_dir), root_name, project_name)
        if not project_dir:
            raise HTTPException(status_code=404, detail=f"Project directory not found for '{project_name}'")

        if decision == "skip":
            skipped_now.add(project_name)
            remove_project_from_layout(layout, project_name)
            remove_project_key_in_index(index, project_name)

            dedup_version_keys.pop(project_name, None)
            dedup_project_keys.pop(project_name, None)
            continue

        if decision == "new_project":
            created = force_register_new_project(conn, user_id, project_name, project_dir, upload_id=upload_id)
            pk = created.get("project_key")
            vk = created.get("version_key")

            if isinstance(pk, int):
                dedup_project_keys[project_name] = pk
            if isinstance(vk, int):
                dedup_version_keys[project_name] = vk
                project_files = [
                    f for f in all_files_info
                    if f.get("project_name") == project_name and f.get("file_type") != "config"
                ]
                for f in project_files:
                    f["version_key"] = int(vk)
                store_parsed_files(conn, project_files, user_id)
                conn.execute(
                    "UPDATE project_versions SET extraction_root = COALESCE(extraction_root, ?) WHERE version_key = ?",
                    (zip_root, int(vk)),
                )
            continue

        if decision == "new_version":
            best_pk = ask_item.get("best_match_project_key")
            existing = ask_item.get("existing")
            if best_pk is None or not existing:
                raise HTTPException(status_code=409, detail=f"Missing best-match info for '{project_name}'")

            created = force_register_new_version(conn, int(best_pk), project_dir, upload_id=upload_id)
            pk = created.get("project_key")
            vk = created.get("version_key")

            if isinstance(vk, int):
                project_files = [
                    f for f in all_files_info
                    if f.get("project_name") == project_name and f.get("file_type") != "config"
                ]
                for f in project_files:
                    f["version_key"] = int(vk)
                store_parsed_files(conn, project_files, user_id)

            if project_name != existing:
                rename_project_in_layout(layout, project_name, existing)
                rename_project_key_in_index(index, project_name, existing)

                renames[project_name] = existing

                # Remove old key entries so later steps use the canonical name.
                dedup_version_keys.pop(project_name, None)
                dedup_project_keys.pop(project_name, None)

            final_name = existing
            if isinstance(pk, int):
                dedup_project_keys[final_name] = pk
            if isinstance(vk, int):
                dedup_version_keys[final_name] = vk
                conn.execute(
                    "UPDATE project_versions SET extraction_root = COALESCE(extraction_root, ?) WHERE version_key = ?",
                    (zip_root, int(vk)),
                )

    prev_skipped = set(state.get("dedup_skipped_projects") or [])
    merged_skipped = sorted(list(prev_skipped | skipped_now))

    state_patch = {
        "layout": layout,
        "dedup_skipped_projects": merged_skipped,
        "dedup_asks": {},  # resolved
        "dedup_resolved": decisions,
        "dedup_renames": renames,
        "project_filetype_index": index,
        "dedup_version_keys": dedup_version_keys,
        "dedup_project_keys": dedup_project_keys,
    }

    conn.commit()

    remaining_projects = set((layout.get("auto_assignments") or {}).keys()) | set(layout.get("pending_projects") or [])
    if not remaining_projects:
        new_state = patch_upload_state(conn, upload_id, patch=state_patch, status="failed")
        return {"upload_id": upload_id, "status": "failed", "zip_name": zip_name, "state": new_state}

    auto_assignments = layout.get("auto_assignments") or {}
    pending_projects = layout.get("pending_projects") or []

    if auto_assignments and not pending_projects:
        # Persist classifications on canonical `projects` rows.
        project_keys = (state.get("dedup_project_keys") or {})
        for project_name, classification in auto_assignments.items():
            pk = project_keys.get(project_name)
            if isinstance(pk, int):
                update_project_metadata(conn, pk, classification=classification)

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

    # Persist chosen classifications on canonical `projects` rows.
    project_keys = (state.get("dedup_project_keys") or {})
    for project_name, classification in assignments.items():
        pk = project_keys.get(project_name)
        if isinstance(pk, int):
            update_project_metadata(conn, pk, classification=classification)

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

    # Prefer canonical keys over display_name (display_name is not unique in schema).
    dedup_project_keys = (state.get("dedup_project_keys") or {}) if isinstance(state, dict) else {}

    for project_name, ptype in project_types.items():
        pk = dedup_project_keys.get(project_name)
        if not isinstance(pk, int):
            # Fallback for older uploads / edge cases where state lacks keys.
            pk = get_project_key(conn, user_id, project_name)
        if not isinstance(pk, int):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

        # Validate via update helper (and update by project_key).
        update_project_metadata(conn, pk, project_type=ptype)

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
    upload_id: int,
):
    """
    Return file rows for this project in this upload (versioned-only files table).
    Scopes by version_key(s) for (project, upload_id), optionally by zip stem in file_path.
    Returns rows as (file_name, file_path, extension, file_type, size_bytes, created, modified);
    callers append project_name when building file items. project_name when building file items.
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        return []
    vrows = conn.execute(
        "SELECT version_key FROM project_versions WHERE project_key = ? AND upload_id = ?",
        (pk, upload_id),
    ).fetchall()
    version_keys = [r[0] for r in vrows]
    if not version_keys:
        return []
    zip_stem = Path(zip_path).stem
    placeholders = ",".join("?" * len(version_keys))

    scoped = conn.execute(
        f"""
        SELECT file_name, file_path, extension, file_type, size_bytes, created, modified
        FROM files
        WHERE user_id = ? AND version_key IN ({placeholders})
          AND (file_path LIKE ? OR file_path LIKE ?)
        ORDER BY file_path ASC
        """,
        (user_id, *version_keys, f"%/{zip_stem}/%", f"{zip_stem}/%"),
    ).fetchall()

    if scoped:
        return scoped

    return conn.execute(
        f"""
        SELECT file_name, file_path, extension, file_type, size_bytes, created, modified
        FROM files
        WHERE user_id = ? AND version_key IN ({placeholders})
        ORDER BY file_path ASC
        """,
        (user_id, *version_keys),
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

    rows = _rows_for_project_scoped_to_upload(conn, user_id, project_name, zip_path, upload_id)

    # build_file_item_from_row expects (..., project_name); files table no longer has project_name
    items = [build_file_item_from_row(Path(ZIP_DATA_DIR), (*r, project_name)) for r in rows]
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

    rows = _rows_for_project_scoped_to_upload(conn, user_id, project_name, zip_path, upload_id)
    valid_relpaths = {
        build_file_item_from_row(Path(ZIP_DATA_DIR), (*r, project_name)).get("relpath") for r in rows
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
