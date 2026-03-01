from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import HTTPException

from src.db.uploads import get_upload_by_id


_SCOPE_VALUES = {"all", "individual", "collaborative"}
_PROJECT_TYPE_VALUES = {"code", "text"}
_CLASSIFICATION_VALUES = {"individual", "collaborative"}


def run_analysis_preflight(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    scope: str,
    force_rerun: bool = False,
) -> dict:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    scope_norm = (scope or "").strip().lower()
    if scope_norm not in _SCOPE_VALUES:
        raise HTTPException(
            status_code=422,
            detail={"invalid_scope": scope, "allowed_scopes": sorted(list(_SCOPE_VALUES))},
        )

    errors, warnings = evaluate_run_readiness(upload, scope_norm)
    if errors:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Upload state is incomplete for analysis run",
                "errors": errors,
            },
        )

    return {
        "upload_id": upload_id,
        "scope": scope_norm,
        "ready": True,
        "warnings": warnings,
    }


def evaluate_run_readiness(upload: dict, scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    status = (upload.get("status") or "").strip().lower()
    state = upload.get("state") or {}
    if not isinstance(state, dict):
        state = {}

    if status == "failed":
        errors.append({"code": "upload_failed"})
        return errors, warnings

    if status == "analyzing":
        errors.append({"code": "analysis_in_progress"})
        return errors, warnings

    dedup_asks = state.get("dedup_asks") or {}
    if isinstance(dedup_asks, dict) and dedup_asks:
        errors.append({"code": "dedup_unresolved", "projects": sorted(dedup_asks.keys())})

    known_projects = _known_projects(state)
    if not known_projects:
        errors.append({"code": "no_projects_detected"})
        return errors, warnings

    classifications = _classifications(state)
    missing_classifications = sorted([p for p in known_projects if p not in classifications])
    if missing_classifications:
        errors.append({"code": "missing_classifications", "projects": missing_classifications})

    projects_in_scope = _projects_in_scope(known_projects, classifications, scope)
    if not projects_in_scope:
        errors.append({"code": "no_projects_in_scope", "scope": scope})
        return errors, warnings

    resolved_types, unresolved_type_projects = _resolved_project_types(state, projects_in_scope)
    if unresolved_type_projects:
        errors.append({"code": "unresolved_project_types", "projects": unresolved_type_projects})

    text_projects = [p for p in projects_in_scope if resolved_types.get(p) == "text"]
    missing_main_file_projects = _missing_main_file_projects(state, text_projects)
    if missing_main_file_projects:
        if len(missing_main_file_projects) == 1:
            errors.append({"code": "missing_main_file", "project": missing_main_file_projects[0]})
        else:
            errors.append({"code": "missing_main_file", "projects": missing_main_file_projects})

    return errors, warnings


def _known_projects(state: dict) -> set[str]:
    projects: set[str] = set()
    dedup_project_keys = state.get("dedup_project_keys") or {}
    if isinstance(dedup_project_keys, dict):
        projects.update([name for name in dedup_project_keys.keys() if isinstance(name, str) and name.strip()])

    layout = state.get("layout") or {}
    if isinstance(layout, dict):
        auto_assignments = layout.get("auto_assignments") or {}
        pending_projects = layout.get("pending_projects") or []
        if isinstance(auto_assignments, dict):
            projects.update([name for name in auto_assignments.keys() if isinstance(name, str) and name.strip()])
        if isinstance(pending_projects, list):
            projects.update([name for name in pending_projects if isinstance(name, str) and name.strip()])

    classifications = state.get("classifications") or {}
    if isinstance(classifications, dict):
        projects.update([name for name in classifications.keys() if isinstance(name, str) and name.strip()])

    project_filetype_index = state.get("project_filetype_index") or {}
    if isinstance(project_filetype_index, dict):
        projects.update([name for name in project_filetype_index.keys() if isinstance(name, str) and name.strip()])

    return projects


def _classifications(state: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    classifications = state.get("classifications") or {}
    if not isinstance(classifications, dict):
        return out

    for project_name, classification in classifications.items():
        if not isinstance(project_name, str) or not project_name.strip():
            continue
        cls_norm = (classification or "").strip().lower()
        if cls_norm in _CLASSIFICATION_VALUES:
            out[project_name] = cls_norm
    return out


def _projects_in_scope(known_projects: set[str], classifications: dict[str, str], scope: str) -> list[str]:
    if scope == "all":
        return sorted(known_projects)

    return sorted([p for p in known_projects if classifications.get(p) == scope])


def _resolved_project_types(state: dict, projects_in_scope: list[str]) -> tuple[dict[str, str], list[str]]:
    resolved: dict[str, str] = {}
    manual_resolved: set[str] = set()

    project_types_auto = state.get("project_types_auto") or {}
    if isinstance(project_types_auto, dict):
        for project_name, project_type in project_types_auto.items():
            ptype_norm = (project_type or "").strip().lower()
            if isinstance(project_name, str) and project_name and ptype_norm in _PROJECT_TYPE_VALUES:
                resolved[project_name] = ptype_norm

    project_types_manual = state.get("project_types_manual") or {}
    if isinstance(project_types_manual, dict):
        for project_name, project_type in project_types_manual.items():
            ptype_norm = (project_type or "").strip().lower()
            if isinstance(project_name, str) and project_name and ptype_norm in _PROJECT_TYPE_VALUES:
                resolved[project_name] = ptype_norm
                manual_resolved.add(project_name)

    unresolved_from_state = set()
    mixed = state.get("project_types_mixed") or []
    unknown = state.get("project_types_unknown") or []
    if isinstance(mixed, list):
        unresolved_from_state.update([p for p in mixed if isinstance(p, str) and p.strip()])
    if isinstance(unknown, list):
        unresolved_from_state.update([p for p in unknown if isinstance(p, str) and p.strip()])

    unresolved = []
    for project_name in projects_in_scope:
        if project_name in unresolved_from_state and project_name not in manual_resolved:
            unresolved.append(project_name)
            continue
        if resolved.get(project_name) not in _PROJECT_TYPE_VALUES:
            unresolved.append(project_name)

    return resolved, sorted(unresolved)


def _missing_main_file_projects(state: dict, text_projects: list[str]) -> list[str]:
    file_roles = state.get("file_roles") or {}
    if not isinstance(file_roles, dict):
        file_roles = {}

    missing: list[str] = []
    for project_name in text_projects:
        project_roles = file_roles.get(project_name) or {}
        if not isinstance(project_roles, dict):
            project_roles = {}
        main_file = project_roles.get("main_file")
        if not isinstance(main_file, str) or not main_file.strip():
            missing.append(project_name)
    return sorted(missing)
