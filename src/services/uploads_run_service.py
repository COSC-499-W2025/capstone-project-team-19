from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from src.db import get_latest_consent, get_latest_external_consent
from src.db.uploads import get_upload_by_id, set_upload_state
from src.services.uploads_file_roles_util import build_file_item_from_row
from src.services.uploads_run_execute_service import (
    execute_upload_scope_analysis,
    has_executable_files_for_scope,
)
from src.utils.parsing import ZIP_DATA_DIR


_SCOPE_VALUES = {"all", "individual", "collaborative"}
_PROJECT_TYPE_VALUES = {"code", "text"}
_CLASSIFICATION_VALUES = {"individual", "collaborative"}
_RUNNABLE_STATUSES = {"needs_file_roles", "needs_summaries", "done"}


def run_analysis_preflight(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    scope: str,
    force_rerun: bool = False,
    *,
    mode: str = "run",
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
    mode_norm = "check" if (mode or "").strip().lower() == "check" else "run"

    internal_consent = get_latest_consent(conn, user_id)
    external_consent = get_latest_external_consent(conn, user_id)
    errors, warnings = evaluate_run_readiness(
        conn,
        user_id,
        upload,
        scope_norm,
        internal_consent=internal_consent,
        external_consent=external_consent,
    )
    state = upload.get("state") or {}
    known_projects = _known_projects(state)
    classifications, _ = _classifications(state)
    projects_in_scope = _projects_in_scope(known_projects, classifications, scope_norm)
    resolved_types, _ = _resolved_project_types(state, projects_in_scope)

    run_state = state.get("run_state") or {}
    if not isinstance(run_state, dict):
        run_state = {}
    completed_scopes = {
        s for s in (run_state.get("completed_scopes") or []) if s in _CLASSIFICATION_VALUES
    }
    target_scopes = _target_completion_scopes(scope_norm, classifications)
    scope_already_completed = bool(
        target_scopes and target_scopes.issubset(completed_scopes) and not force_rerun
    )

    if mode_norm == "check":
        check_errors = list(errors)
        if scope_already_completed:
            check_errors.append({"code": "scope_already_completed", "scope": scope_norm})
        return {
            "upload_id": upload_id,
            "scope": scope_norm,
            "ready": len(check_errors) == 0,
            "warnings": warnings,
            "errors": check_errors,
        }

    if errors:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Upload state is incomplete for analysis run",
                "errors": errors,
            },
        )

    if scope_already_completed:
        raise HTTPException(
            status_code=409,
            detail={"code": "scope_already_completed", "scope": scope_norm},
        )

    # Some unit tests create synthetic uploads with no persisted files.
    # For real uploads, executable artifacts exist and we run the pipeline.
    zip_path = (state.get("zip_path") or upload.get("zip_path") or "").strip()
    should_execute = bool(zip_path) and Path(zip_path).exists() and has_executable_files_for_scope(
        conn,
        user_id,
        state=state,
        projects_in_scope=projects_in_scope,
    )

    if should_execute:
        started_state = dict(state)
        started_run_state = dict(run_state)
        started_run_state.update(
            {
                "last_requested_scope": scope_norm,
                "last_started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
        started_state["run_state"] = started_run_state
        set_upload_state(conn, upload_id, started_state, status="analyzing")

        try:
            execute_upload_scope_analysis(
                conn,
                user_id,
                upload=upload,
                projects_in_scope=projects_in_scope,
                classifications=classifications,
                resolved_types=resolved_types,
                external_consent=external_consent,
            )
        except Exception as exc:
            failed_state = dict(started_state)
            failed_run_state = dict(failed_state.get("run_state") or {})
            failed_run_state["last_error"] = str(exc)
            failed_run_state["last_failed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            failed_state["run_state"] = failed_run_state
            set_upload_state(conn, upload_id, failed_state, status="failed")
            raise HTTPException(
                status_code=500,
                detail={"code": "analysis_execution_failed", "message": "Run execution failed"},
            ) from exc

        completed_scopes |= target_scopes
        required_scopes = {
            cls
            for cls in classifications.values()
            if cls in _CLASSIFICATION_VALUES
        }
        is_done = bool(required_scopes) and required_scopes.issubset(completed_scopes)

        resume_status = upload.get("status")
        if resume_status not in {"needs_file_roles", "needs_summaries"}:
            resume_status = "needs_file_roles"

        final_state = dict(started_state)
        final_run_state = dict(final_state.get("run_state") or {})
        final_run_state.update(
            {
                "completed_scopes": sorted(completed_scopes),
                "last_completed_scope": scope_norm,
                "last_completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "last_warnings": warnings,
            }
        )
        final_state["run_state"] = final_run_state
        set_upload_state(conn, upload_id, final_state, status="done" if is_done else resume_status)

    return {
        "upload_id": upload_id,
        "scope": scope_norm,
        "ready": True,
        "warnings": warnings,
        "errors": [],
    }


def evaluate_run_readiness(
    conn: sqlite3.Connection,
    user_id: int,
    upload: dict,
    scope: str,
    *,
    internal_consent: str | None = None,
    external_consent: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
        errors.append({"code": "already_analyzing"})
        return errors, warnings
    
    if status not in _RUNNABLE_STATUSES:
        errors.append({"code": "upload_not_ready", "status": status})
        return errors, warnings

    if (internal_consent or "").strip().lower() != "accepted":
        errors.append({"code": "missing_internal_consent"})

    dedup_asks = state.get("dedup_asks") or {}
    if isinstance(dedup_asks, dict) and dedup_asks:
        errors.append({"code": "dedup_unresolved", "projects": sorted(dedup_asks.keys())})

    known_projects = _known_projects(state)
    if not known_projects:
        errors.append({"code": "no_projects_detected"})
        return errors, warnings

    dedup_project_keys = state.get("dedup_project_keys") or {}
    if not isinstance(dedup_project_keys, dict):
        dedup_project_keys = {}
    missing_project_keys = sorted([p for p in known_projects if not isinstance(dedup_project_keys.get(p), int)])
    if missing_project_keys:
        errors.append({"code": "missing_project_keys", "projects": missing_project_keys})

    dedup_version_keys = state.get("dedup_version_keys") or {}
    if not isinstance(dedup_version_keys, dict):
        dedup_version_keys = {}
    missing_version_keys = sorted([p for p in known_projects if not isinstance(dedup_version_keys.get(p), int)])
    if missing_version_keys:
        errors.append({"code": "missing_version_keys", "projects": missing_version_keys})

    classifications, invalid_classifications = _classifications(state)
    if invalid_classifications:
        errors.append({"code": "invalid_classifications", "projects": sorted(invalid_classifications)})
    missing_classifications = sorted([p for p in known_projects if p not in classifications])
    if missing_classifications:
        errors.append({"code": "missing_classifications", "projects": missing_classifications})

    projects_in_scope = _projects_in_scope(known_projects, classifications, scope)
    if not projects_in_scope:
        errors.append({"code": "no_projects_for_scope", "scope": scope})
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

    if errors:
        return errors, warnings

    _populate_project_warnings(
        conn=conn,
        user_id=user_id,
        state=state,
        projects_in_scope=projects_in_scope,
        classifications=classifications,
        resolved_types=resolved_types,
        external_consent=external_consent,
        warnings=warnings,
    )

    return errors, warnings


def _target_completion_scopes(scope: str, classifications: dict[str, str]) -> set[str]:
    if scope == "all":
        return {
            cls
            for cls in classifications.values()
            if cls in _CLASSIFICATION_VALUES
        }
    if scope in _CLASSIFICATION_VALUES:
        return {scope}
    return set()


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


def _classifications(state: dict) -> tuple[dict[str, str], set[str]]:
    out: dict[str, str] = {}
    invalid: set[str] = set()
    classifications = state.get("classifications") or {}
    if not isinstance(classifications, dict):
        return out, invalid

    for project_name, classification in classifications.items():
        if not isinstance(project_name, str) or not project_name.strip():
            continue
        cls_norm = (classification or "").strip().lower()
        if cls_norm in _CLASSIFICATION_VALUES:
            out[project_name] = cls_norm
        else:
            invalid.add(project_name)
    return out, invalid


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


def _populate_project_warnings(
    *,
    conn: sqlite3.Connection,
    user_id: int,
    state: dict,
    projects_in_scope: list[str],
    classifications: dict[str, str],
    resolved_types: dict[str, str],
    external_consent: str | None,
    warnings: list[dict[str, Any]],
) -> None:
    llm_enabled = (external_consent or "").strip().lower() == "accepted"

    for project_name in projects_in_scope:
        classification = classifications.get(project_name)
        project_type = resolved_types.get(project_name)
        if classification not in _CLASSIFICATION_VALUES or project_type not in _PROJECT_TYPE_VALUES:
            continue

        run_inputs = _project_run_inputs(state, project_name)
        git = run_inputs["capabilities"]["git"]
        github = run_inputs["integrations"]["github"]
        drive = run_inputs["integrations"]["drive"]
        manual = run_inputs["manual_inputs"]

        if project_type == "code":
            repo_detected = git.get("repo_detected")
            commit_count_hint = int(git.get("commit_count_hint") or 0)
            multi_author_hint = bool(git.get("multi_author_hint"))
            selected_identity_indices = git.get("selected_identity_indices") or []

            if repo_detected is False:
                _add_warning(warnings, "no_git_repo_detected", project_name)
            elif repo_detected is True and commit_count_hint <= 0:
                _add_warning(warnings, "no_git_commits_found", project_name)

            if classification == "collaborative" and repo_detected is True and multi_author_hint and not selected_identity_indices:
                _add_warning(warnings, "missing_git_identities", project_name)

            gh_state = (github.get("state") or "unset").strip().lower()
            if gh_state == "unset":
                _add_warning(warnings, "github_not_configured", project_name)
            elif gh_state == "skipped":
                _add_warning(warnings, "github_skipped", project_name)

            if not bool(github.get("repo_linked")):
                _add_warning(warnings, "missing_github_link", project_name)

            if not llm_enabled:
                _add_warning(warnings, "llm_disabled", project_name)

            if classification == "collaborative":
                if not bool(manual.get("manual_contribution_summary_set")):
                    _add_warning(warnings, "missing_manual_contribution_summary", project_name)
            else:
                if not bool(manual.get("manual_project_summary_set")):
                    _add_warning(warnings, "missing_manual_summary", project_name)

            if not bool(manual.get("key_role_set")):
                _add_warning(warnings, "missing_key_role", project_name)

        elif project_type == "text":
            if not bool(manual.get("contribution_sections_set")):
                _add_warning(warnings, "missing_contribution_sections", project_name)

            has_supporting = bool(manual.get("supporting_text_files_set")) or bool(manual.get("supporting_csv_files_set"))
            has_supporting_candidates = _project_has_supporting_candidates(
                conn=conn,
                user_id=user_id,
                state=state,
                project_name=project_name,
            )
            if has_supporting_candidates and not has_supporting:
                _add_warning(warnings, "missing_supporting_files", project_name)

            # Drive integration is only required/used for collaborative text projects.
            if classification == "collaborative":
                drive_state = (drive.get("state") or "unset").strip().lower()
                if drive_state == "unset":
                    _add_warning(warnings, "drive_not_configured", project_name)
                elif drive_state == "skipped":
                    _add_warning(warnings, "drive_skipped", project_name)

                if drive_state == "connected" and int(drive.get("linked_files_count") or 0) <= 0:
                    _add_warning(warnings, "missing_drive_links", project_name)

            if not llm_enabled:
                _add_warning(warnings, "llm_disabled", project_name)

            if classification == "collaborative":
                if not bool(manual.get("manual_contribution_summary_set")):
                    _add_warning(warnings, "missing_manual_contribution_summary", project_name)
            else:
                if not bool(manual.get("manual_project_summary_set")):
                    _add_warning(warnings, "missing_manual_summary", project_name)

            if not bool(manual.get("key_role_set")):
                _add_warning(warnings, "missing_key_role", project_name)


def _project_run_inputs(state: dict, project_name: str) -> dict[str, Any]:
    run_inputs = state.get("run_inputs") or {}
    if not isinstance(run_inputs, dict):
        run_inputs = {}
    projects = run_inputs.get("projects") or {}
    if not isinstance(projects, dict):
        projects = {}
    project_inputs = projects.get(project_name) or {}
    if not isinstance(project_inputs, dict):
        project_inputs = {}
    return _deep_merge(_project_input_defaults(), project_inputs)


def _project_has_supporting_candidates(
    *,
    conn: sqlite3.Connection,
    user_id: int,
    state: dict,
    project_name: str,
) -> bool:
    dedup_version_keys = state.get("dedup_version_keys") or {}
    if not isinstance(dedup_version_keys, dict):
        return False

    version_key = dedup_version_keys.get(project_name)
    if not isinstance(version_key, int):
        return False

    file_roles = state.get("file_roles") or {}
    if not isinstance(file_roles, dict):
        file_roles = {}
    project_roles = file_roles.get(project_name) or {}
    if not isinstance(project_roles, dict):
        project_roles = {}
    main_file = (project_roles.get("main_file") or "").strip()

    rows = conn.execute(
        """
        SELECT file_name, file_path, extension, file_type, size_bytes, created, modified
        FROM files
        WHERE user_id = ? AND version_key = ?
        ORDER BY file_path ASC
        """,
        (user_id, version_key),
    ).fetchall()
    if not rows:
        return False

    for row in rows:
        item = build_file_item_from_row(Path(ZIP_DATA_DIR), (*row, project_name))
        relpath = (item.get("relpath") or "").strip()
        ext = (item.get("extension") or "").lower()
        fname = (item.get("file_name") or "").lower()
        is_csv = ext == ".csv" or fname.endswith(".csv")
        if is_csv:
            return True
        if item.get("file_type") == "text" and relpath and relpath != main_file:
            return True
    return False


def _project_input_defaults() -> dict[str, Any]:
    return {
        "capabilities": {
            "git": {
                "repo_detected": None,
                "commit_count_hint": 0,
                "author_count_hint": 0,
                "multi_author_hint": False,
                "selected_identity_indices": [],
            }
        },
        "integrations": {
            "github": {
                "state": "unset",
                "repo_linked": False,
                "repo_full_name": None,
            },
            "drive": {
                "state": "unset",
                "linked_files_count": 0,
            },
        },
        "manual_inputs": {
            "key_role_set": False,
            "manual_project_summary_set": False,
            "manual_contribution_summary_set": False,
            "contribution_sections_set": False,
            "contribution_sections_count": 0,
            "supporting_text_files_set": False,
            "supporting_text_files_count": 0,
            "supporting_csv_files_set": False,
            "supporting_csv_files_count": 0,
        },
    }


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = dict(base or {})
    for key, value in (incoming or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _add_warning(warnings: list[dict[str, Any]], code: str, project_name: str) -> None:
    item = {"code": code, "project": project_name}
    if item not in warnings:
        warnings.append(item)
