from __future__ import annotations

import sqlite3
from typing import Any

from src.db.uploads import get_upload_by_id, set_upload_state


def merge_project_run_inputs(
    conn: sqlite3.Connection,
    upload_id: int,
    project_name: str,
    patch: dict[str, Any],
) -> None:
    """
    Merge per-project run input signals into uploads.state.run_inputs.projects.
    Best-effort helper: silently no-ops if upload/project_name is missing.
    """
    if not project_name:
        return

    upload = get_upload_by_id(conn, upload_id)
    if not upload:
        return

    state = dict(upload.get("state") or {})
    run_inputs = dict(state.get("run_inputs") or {})
    projects = dict(run_inputs.get("projects") or {})
    current = dict(projects.get(project_name) or {})
    current = _deep_merge(_project_defaults(), current)

    projects[project_name] = _deep_merge(current, patch or {})
    run_inputs["projects"] = projects
    state["run_inputs"] = run_inputs

    set_upload_state(conn, upload_id, state, status=upload.get("status"))


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = dict(base or {})
    for key, value in (incoming or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _project_defaults() -> dict[str, Any]:
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
