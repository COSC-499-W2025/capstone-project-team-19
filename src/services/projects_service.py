import json
from typing import List, Dict, Any, Optional
from src.db.project_summaries import get_project_summaries_list, get_project_summary_by_id
from src.db.delete_project import delete_project_everywhere, delete_all_user_projects


def list_projects(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing projects. DB access belongs here, not in routes.
    """
    return get_project_summaries_list(conn, user_id)


def get_project_by_id(conn, user_id: int, project_summary_id: int) -> Optional[Dict[str, Any]]:
    """
    Service method for retrieving a project by its ID.
    """
    row = get_project_summary_by_id(conn, user_id, project_summary_id)
    if not row:
        return None

    # Parse the summary_json
    try:
        summary_dict = json.loads(row["summary_json"])
    except json.JSONDecodeError:
        summary_dict = {}

    row_without_json = {k: v for k, v in row.items() if k != "summary_json"}
    manual_overrides = summary_dict.get("manual_overrides") or {}

    result = {**row_without_json, **summary_dict}

    # Apply summary_text override so the detail view reflects the edited value
    if manual_overrides.get("summary_text") is not None:
        result["summary_text"] = manual_overrides["summary_text"]

    return result


def delete_project(conn, user_id: int, project_id: int, refresh_resumes: bool = False) -> bool:
    """
    Delete a single project by ID.
    Returns True if deleted, False if not found.
    If refresh_resumes is True, also remove the project from resume snapshots.
    """
    row = get_project_summary_by_id(conn, user_id, project_id)
    if not row:
        return False

    project_name = row["project_name"]
    delete_project_everywhere(conn, user_id, project_name)

    if refresh_resumes:
        from src.menu.resume.resume import refresh_saved_resumes_after_project_delete
        refresh_saved_resumes_after_project_delete(conn, user_id, project_name)

    return True


def edit_project_summary(
    conn,
    user_id: int,
    project_summary_id: int,
    summary_text: Optional[str] = None,
    contribution_summary: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    row = get_project_summary_by_id(conn, user_id, project_summary_id)
    if not row:
        return None

    project_name = row["project_name"]
    nothing_to_do = summary_text is None and contribution_summary is None

    if nothing_to_do:
        return get_project_by_id(conn, user_id, project_summary_id)

    # Update summary_text via manual_overrides (fans out to resumes)
    if summary_text is not None:
        from src.services.resume_overrides import update_project_manual_overrides, apply_manual_overrides_to_resumes
        manual_overrides = update_project_manual_overrides(
            conn, user_id, project_name, {"summary_text": summary_text or None}
        )
        if manual_overrides is not None:
            apply_manual_overrides_to_resumes(
                conn, user_id, project_name, manual_overrides, {"summary_text"}
            )

    # Update contribution_summary directly in summary_json.contributions
    if contribution_summary is not None:
        from src.db.project_summaries import get_project_summary_by_name
        from src.db import update_project_summary_json
        summary_row = get_project_summary_by_name(conn, user_id, project_name)
        if summary_row:
            try:
                summary_dict = json.loads(summary_row["summary_json"])
            except Exception:
                summary_dict = {}
            contributions = dict(summary_dict.get("contributions") or {})
            if contribution_summary:
                contributions["manual_contribution_summary"] = contribution_summary
            else:
                contributions.pop("manual_contribution_summary", None)
            summary_dict["contributions"] = contributions
            update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))

    return get_project_by_id(conn, user_id, project_summary_id)


def delete_all_projects(conn, user_id: int, refresh_resumes: bool = False) -> int:
    """
    Delete all projects for a user.
    Returns the count of deleted projects.
    If refresh_resumes is True, also remove the projects from resume snapshots.
    """
    # Collect project names BEFORE deletion (needed for resume refresh)
    if refresh_resumes:
        summaries = get_project_summaries_list(conn, user_id)
        project_names = [s["project_name"] for s in summaries]

    count = delete_all_user_projects(conn, user_id)

    if refresh_resumes and count > 0:
        from src.menu.resume.resume import refresh_saved_resumes_after_project_delete
        for project_name in project_names:
            refresh_saved_resumes_after_project_delete(conn, user_id, project_name)

    return count