from __future__ import annotations

from sqlite3 import Connection

from fastapi import HTTPException

from src.db.projects import get_project_for_upload_by_key
from src.db.uploads import get_upload_by_id


_READY_STATUSES = {"needs_file_roles", "needs_summaries"}
_ALLOWED_CLASSIFICATIONS = {"individual", "collaborative"}
_ALLOWED_PROJECT_TYPES = {"code", "text"}


def validate_upload_run_readiness(
    conn: Connection,
    user_id: int,
    upload_id: int,
    *,
    scope: str,
    force_rerun: bool,
) -> dict:
    """
    Validate whether an upload has enough state to start analysis.

    This is route/service-level readiness validation only.
    Actual analysis execution is wired in follow-up changes.
    """
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    status = (upload.get("status") or "").strip()

    if status == "analyzing":
        raise HTTPException(status_code=409, detail="Upload is already analyzing")

    if status == "done" and not force_rerun:
        raise HTTPException(
            status_code=409,
            detail="Upload analysis is already completed. Set force_rerun=true to run again.",
        )

    if status not in _READY_STATUSES and not (status == "done" and force_rerun):
        raise HTTPException(status_code=409, detail=f"Upload not ready for run (status={status})")

    state = upload.get("state") or {}
    errors: list[dict] = []

    classifications = state.get("classifications")
    if not isinstance(classifications, dict) or not classifications:
        errors.append({"code": "missing_classifications"})
        classifications = {}
    else:
        bad = {k: v for k, v in classifications.items() if v not in _ALLOWED_CLASSIFICATIONS}
        if bad:
            errors.append({"code": "invalid_classifications", "items": bad})

    project_keys = state.get("dedup_project_keys")
    if not isinstance(project_keys, dict) or not project_keys:
        errors.append({"code": "missing_project_keys"})
        project_keys = {}

    version_keys = state.get("dedup_version_keys")
    if not isinstance(version_keys, dict) or not version_keys:
        errors.append({"code": "missing_version_keys"})
        version_keys = {}

    unresolved_types = sorted(
        set(state.get("project_types_mixed") or []) | set(state.get("project_types_unknown") or [])
    )
    if unresolved_types:
        errors.append({"code": "unresolved_project_types", "projects": unresolved_types})

    if scope == "all":
        target_projects = list(classifications.keys())
    else:
        target_projects = [name for name, cls in classifications.items() if cls == scope]
        if not target_projects:
            errors.append({"code": "no_projects_for_scope", "scope": scope})

    file_roles = state.get("file_roles") or {}
    if not isinstance(file_roles, dict):
        file_roles = {}

    for project_name in target_projects:
        pk = project_keys.get(project_name)
        if not isinstance(pk, int):
            errors.append({"code": "missing_project_key", "project": project_name})
            continue

        vk = version_keys.get(project_name)
        if not isinstance(vk, int):
            errors.append({"code": "missing_version_key", "project": project_name})

        project_row = get_project_for_upload_by_key(conn, user_id, pk, upload_id)
        if not project_row:
            errors.append({"code": "project_not_in_upload", "project": project_name, "project_key": pk})
            continue

        project_type = project_row.get("project_type")
        if project_type not in _ALLOWED_PROJECT_TYPES:
            errors.append({"code": "missing_project_type", "project": project_name})
            continue

        if project_type == "text":
            project_roles = file_roles.get(project_name) or {}
            main_file = project_roles.get("main_file") if isinstance(project_roles, dict) else None
            if not isinstance(main_file, str) or not main_file.strip():
                errors.append({"code": "missing_main_file", "project": project_name})

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Upload state is incomplete for analysis run",
                "errors": errors,
            },
        )

    return {
        "upload_id": upload_id,
        "status": upload["status"],
        "scope": scope,
        "accepted": True,
        "message": "Upload is ready for analysis run.",
    }
