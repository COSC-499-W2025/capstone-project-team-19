from typing import List, Dict, Any, Optional, Literal
from src.db.resumes import (
    list_resumes,
    get_resume_snapshot,
    update_resume_snapshot,
    delete_resume_snapshot,
    delete_all_user_resumes,
)
from src.menu.resume.helpers import (
    render_snapshot,
    apply_resume_only_updates,
    resolve_resume_contribution_bullets,
    recompute_aggregated_skills,
)
from src.menu.resume.date_helpers import enrich_snapshot_with_dates
from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.services.resume_generation import (
    build_resume_snapshot_data,
    insert_resume_snapshot_record,
    load_all_project_summaries,
    load_project_summaries_by_ids,
    select_ranked_summaries,
)
from src.services.resume_overrides import (
    update_project_manual_overrides,
    apply_manual_overrides_to_resumes,
)
import json


def list_user_resumes(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing resumes.
    """
    return list_resumes(conn, user_id)

def get_resume_by_id(conn, user_id: int, resume_id: int) -> Optional[Dict[str, Any]]:
    """
    Service method for retrieving a resume by its ID.
    Parses resume_json and flattens it into the response.
    """
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None
    
    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        snapshot = {}
    
    # Combine DB fields with parsed JSON
    return {
        "id": record["id"],
        "name": record["name"],
        "created_at": record["created_at"],
        "rendered_text": record.get("rendered_text"),
        **snapshot  # projects, aggregated_skills
    }

def generate_resume(
    conn,
    user_id: int,
    name: str,
    project_ids: Optional[List[int]] = None,
) -> Optional[Dict[str, Any]]:
    if project_ids:
        summaries = load_project_summaries_by_ids(conn, user_id, project_ids)
    else:
        # No project_ids provided - use top 5 ranked projects (like menu flow)
        ranked = collect_project_data(conn, user_id)
        if not ranked:
            return None

        all_summaries = load_all_project_summaries(conn, user_id)
        summaries, _selected_names = select_ranked_summaries(all_summaries, ranked)

    snapshot_data = build_resume_snapshot_data(conn, user_id, summaries, print_output=False)
    if not snapshot_data:
        return None
    snapshot, rendered = snapshot_data

    resume_id = insert_resume_snapshot_record(conn, user_id, name, snapshot, rendered)
    return get_resume_by_id(conn, user_id, resume_id)

def edit_resume(
    conn,
    user_id: int,
    resume_id: int,
    project_name: Optional[str] = None,
    scope: Optional[Literal["resume_only", "global"]] = None,
    name: Optional[str] = None,
    display_name: Optional[str] = None,
    summary_text: Optional[str] = None,
    contribution_bullets: Optional[List[str]] = None,
    contribution_edit_mode: Literal["append", "replace"] = "replace",
    key_role: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    # Get the resume record
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None

    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        return None

    # Update resume name if provided
    if name is not None:
        conn.execute(
            "UPDATE resume_snapshots SET name = ? WHERE user_id = ? AND id = ?",
            (name, user_id, resume_id),
        )
        conn.commit()

    # If no project_name provided, just return after name update (name-only edit)
    if project_name is None:
        return get_resume_by_id(conn, user_id, resume_id)

    # For project editing, scope is required
    if scope is None:
        scope = "resume_only"  # Default to resume_only if not specified

    # Find the project entry in the snapshot
    projects = snapshot.get("projects") or []
    project_entry = None
    for p in projects:
        if p.get("project_name") == project_name:
            project_entry = p
            break

    if not project_entry:
        return None

    # Build updates dict
    updates: Dict[str, Any] = {}
    if display_name is not None:
        updates["display_name"] = display_name or None
    if summary_text is not None:
        updates["summary_text"] = summary_text or None
    if contribution_bullets is not None:
        if contribution_edit_mode == "append" and contribution_bullets:
            # Append new bullets to existing ones
            current_bullets = resolve_resume_contribution_bullets(project_entry)
            updates["contribution_bullets"] = current_bullets + contribution_bullets
        else:
            # Replace mode: use provided bullets directly
            updates["contribution_bullets"] = contribution_bullets or None
    if key_role is not None:
        updates["key_role"] = key_role or None

    if not updates:
        # No field updates, just return existing
        return get_resume_by_id(conn, user_id, resume_id)

    if scope == "resume_only":
        # Apply resume-only overrides
        apply_resume_only_updates(project_entry, updates)
        rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
        updated_json = json.dumps(snapshot, default=str)
        update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)

    else:  # scope == "global"
        # Update project_summaries and fan out to all resumes
        manual_overrides = update_project_manual_overrides(conn, user_id, project_name, updates)
        if manual_overrides is not None:
            apply_manual_overrides_to_resumes(
                conn,
                user_id,
                project_name,
                manual_overrides,
                set(updates.keys()),
                force_resume_id=resume_id,
            )

    return get_resume_by_id(conn, user_id, resume_id)


def delete_resume(conn, user_id: int, resume_id: int) -> bool:
    """
    Delete a single resume by ID.
    Returns True if deleted, False if not found.
    """
    return delete_resume_snapshot(conn, user_id, resume_id)


def delete_all_resumes(conn, user_id: int) -> int:
    """
    Delete all resumes for a user.
    Returns the count of deleted resumes.
    """
    return delete_all_user_resumes(conn, user_id)


def remove_project_from_resume(
    conn, user_id: int, resume_id: int, project_name: str
) -> Optional[Dict[str, Any]]:
    """
    Remove a single project from a resume snapshot.

    Returns:
      - Updated resume dict if project was removed and resume still has projects.
      - {"deleted_resume": True} if the resume was deleted because no projects remained.
      - None if the resume was not found or the project was not in the resume.
    """
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None

    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        return None

    projects = snapshot.get("projects") or []
    original_len = len(projects)
    new_projects = [p for p in projects if p.get("project_name") != project_name]

    if len(new_projects) == original_len:
        # Project was not in this resume.
        return None

    if not new_projects:
        delete_resume_snapshot(conn, user_id, resume_id)
        return {"deleted_resume": True}

    snapshot["projects"] = new_projects
    snapshot["aggregated_skills"] = recompute_aggregated_skills(new_projects)
    snapshot = enrich_snapshot_with_dates(conn, user_id, snapshot)
    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
    updated_json = json.dumps(snapshot, default=str)
    update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)

    return get_resume_by_id(conn, user_id, resume_id)
