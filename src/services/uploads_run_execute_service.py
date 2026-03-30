from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.models.project_summary import ProjectSummary
from src.project_analysis import (
    get_individual_contributions,
    run_individual_analysis,
    _load_skills_into_summary,
    _load_text_activity_type_into_summary,
    _load_text_metrics_into_summary,
)
from src.db.project_summaries import save_project_summary
from src.analysis.code_collaborative.code_collaborative_analysis import print_code_portfolio_summary


def execute_upload_scope_analysis(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    upload: dict,
    projects_in_scope: list[str],
    classifications: dict[str, str],
    resolved_types: dict[str, str],
    external_consent: str | None,
) -> dict[str, Any]:
    """
    Execute analysis for all projects in scope in non-interactive API mode.
    Assumes readiness checks have already passed.
    """
    state = upload.get("state") or {}
    zip_path = upload.get("zip_path") or state.get("zip_path")
    if not isinstance(zip_path, str) or not zip_path.strip():
        raise ValueError("missing zip_path")

    executed_projects: list[str] = []
    ran_collab_code = False

    for project_name in projects_in_scope:
        project_type = resolved_types.get(project_name)
        classification = classifications.get(project_name)
        if project_type not in {"code", "text"}:
            continue
        if classification not in {"individual", "collaborative"}:
            continue

        summary = ProjectSummary(
            project_name=project_name,
            project_type=project_type,
            project_mode=classification,
        )

        version_key = (state.get("dedup_version_keys") or {}).get(project_name)
        api_inputs = _build_project_api_inputs(state, project_name)

        if classification == "individual":
            run_individual_analysis(
                conn,
                user_id,
                project_name,
                project_type,
                external_consent,
                zip_path,
                summary,
                version_key=version_key,
                allow_prompts=False,
                api_inputs=api_inputs,
            )
            _load_skills_into_summary(conn, user_id, project_name, summary)
            _load_text_metrics_into_summary(conn, user_id, project_name, summary)
            if project_type == "text":
                _load_text_activity_type_into_summary(
                    conn,
                    user_id,
                    project_name,
                    summary,
                    is_collaborative=False,
                )
        else:
            get_individual_contributions(
                conn,
                user_id,
                project_name,
                project_type,
                external_consent,
                zip_path,
                summary,
                version_key=version_key,
                allow_prompts=False,
                api_inputs=api_inputs,
            )
            _load_skills_into_summary(conn, user_id, project_name, summary)
            _load_text_metrics_into_summary(conn, user_id, project_name, summary)
            if project_type == "text":
                _load_text_activity_type_into_summary(
                    conn,
                    user_id,
                    project_name,
                    summary,
                    is_collaborative=True,
                )
            if project_type == "code":
                ran_collab_code = True

        save_project_summary(conn, user_id, project_name, json.dumps(summary.__dict__, default=str))
        executed_projects.append(project_name)

    if ran_collab_code:
        # Clear run-level aggregator used by collaborative code analysis.
        print_code_portfolio_summary()

    return {
        "executed_projects": executed_projects,
        "executed_count": len(executed_projects),
    }


def has_executable_files_for_scope(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    state: dict,
    projects_in_scope: list[str],
) -> bool:
    version_keys = []
    dedup_version_keys = state.get("dedup_version_keys") or {}
    if not isinstance(dedup_version_keys, dict):
        dedup_version_keys = {}

    for project_name in projects_in_scope:
        vk = dedup_version_keys.get(project_name)
        if isinstance(vk, int):
            version_keys.append(vk)

    if not version_keys:
        return False

    placeholders = ",".join("?" * len(version_keys))
    row = conn.execute(
        f"SELECT COUNT(1) FROM files WHERE user_id = ? AND version_key IN ({placeholders})",
        (user_id, *version_keys),
    ).fetchone()
    return bool(row and int(row[0]) > 0)


def _build_project_api_inputs(state: dict, project_name: str) -> dict[str, Any]:
    run_inputs = state.get("run_inputs") or {}
    if not isinstance(run_inputs, dict):
        run_inputs = {}
    projects = run_inputs.get("projects") or {}
    if not isinstance(projects, dict):
        projects = {}
    project_inputs = projects.get(project_name) or {}
    if not isinstance(project_inputs, dict):
        project_inputs = {}

    contributions = state.get("contributions") or {}
    if not isinstance(contributions, dict):
        contributions = {}

    # contributions may be keyed by project_name OR by str(project_key)
    # the manual summaries service saves by str(project_key), so check both
    dedup_project_keys = state.get("dedup_project_keys") or {}
    project_key = dedup_project_keys.get(project_name)
    project_key_str = str(project_key) if project_key is not None else None

    project_contrib = contributions.get(project_name) or {}
    if not isinstance(project_contrib, dict):
        project_contrib = {}

    # merge in key-keyed contributions (manual summaries service writes here)
    if project_key_str:
        key_contrib = contributions.get(project_key_str) or {}
        if isinstance(key_contrib, dict):
            # key-keyed values take precedence since they come from the summaries service
            project_contrib = {**project_contrib, **key_contrib}
        
    # DEBUG STAETEMENT
    print(f"[DEBUG] contributions keys: {list(contributions.keys())}")
    print(f"[DEBUG] main_section_ids for {project_name!r}: {project_contrib.get('main_section_ids')}")

    file_roles = state.get("file_roles") or {}
    if not isinstance(file_roles, dict):
        file_roles = {}
    project_roles = file_roles.get(project_name) or {}
    if not isinstance(project_roles, dict):
        project_roles = {}

    out = dict(project_inputs)
    out["main_file_relpath"] = project_roles.get("main_file")
    out["main_section_ids"] = project_contrib.get("main_section_ids") or []
    derived_sections = state.get("derived_sections") or {}
    project_derived = derived_sections.get(project_name) or {}
    out["cached_sections"] = project_derived.get("sections") or []

    out["supporting_text_relpaths"] = project_contrib.get("supporting_text_relpaths") or []
    out["supporting_csv_relpaths"] = project_contrib.get("supporting_csv_relpaths") or []
    # manual_project_summaries is a separate top-level key written by set_manual_project_summary
    manual_project_summaries = state.get("manual_project_summaries") or {}
    out["manual_project_summary"] = (
        (manual_project_summaries.get(project_key_str) if project_key_str else None)
        or project_contrib.get("manual_project_summary")
    )
    out["manual_contribution_summary"] = project_contrib.get("manual_contribution_summary")
    out["key_role"] = project_contrib.get("key_role")
    print(f"[DEBUG api_inputs] project={project_name!r}")
    print(f"[DEBUG api_inputs] manual_project_summary={out.get('manual_project_summary')!r}")
    print(f"[DEBUG api_inputs] manual_contribution_summary={out.get('manual_contribution_summary')!r}")
    print(f"[DEBUG api_inputs] project_key_str={project_key_str!r}")
    print(f"[DEBUG api_inputs] manual_project_summaries keys={list((state.get('manual_project_summaries') or {}).keys())}")
    return out
