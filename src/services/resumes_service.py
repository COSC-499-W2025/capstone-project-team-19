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
    resolve_resume_display_name,
    resolve_resume_summary_text,
    resolve_resume_key_role,
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
from src.services.skill_preferences_service import (
    update_skill_preferences,
    reset_skill_preferences,
    normalize_skill_preferences,
    get_highlighted_skills_for_display,
)
from src.db.skill_preferences import (
    has_skill_preferences,
    get_all_user_skills,
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
    Filters aggregated_skills based on user skill preferences.
    """
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None

    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        snapshot = {}

    # Apply skill preference filtering if user has any preferences
    if has_skill_preferences(conn, user_id, "resume", context_id=resume_id) or \
       has_skill_preferences(conn, user_id, "global"):
        highlighted = set(get_highlighted_skills_for_display(
            conn, user_id, context="resume", context_id=resume_id
        ))
        agg = snapshot.get("aggregated_skills", {})
        agg["technical_skills"] = [s for s in agg.get("technical_skills", []) if s in highlighted]
        agg["writing_skills"] = [s for s in agg.get("writing_skills", []) if s in highlighted]
        snapshot["aggregated_skills"] = agg
        for project in snapshot.get("projects", []):
            if "skills" in project:
                project["skills"] = [s for s in project["skills"] if s in highlighted]

    # Resolve overrides so the API returns the effective values
    for project in snapshot.get("projects", []):
        project["project_name"] = resolve_resume_display_name(project)
        project["summary_text"] = resolve_resume_summary_text(project)
        project["contribution_bullets"] = resolve_resume_contribution_bullets(project)
        project["key_role"] = resolve_resume_key_role(project)

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
    skill_preferences: Optional[List[Dict[str, Any]]] = None,
    skill_preferences_reset: Optional[bool] = False,
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

    # Resume-level skill preferences (not per project)
    prefs_changed = False
    if skill_preferences_reset:
        reset_skill_preferences(
            conn,
            user_id,
            context="resume",
            context_id=resume_id,
            project_key=None,
        )
        prefs_changed = True
    elif skill_preferences:
        normalized_prefs = normalize_skill_preferences(skill_preferences)
        if normalized_prefs:
            # Validate skill names against actual user skills
            valid_skills = set(get_all_user_skills(conn, user_id))
            invalid = [p["skill_name"] for p in normalized_prefs if p["skill_name"] not in valid_skills]
            if invalid:
                raise ValueError(f"Invalid skill name(s): {', '.join(invalid)}")
            update_skill_preferences(
                conn,
                user_id,
                normalized_prefs,
                context="resume",
                context_id=resume_id,
                project_key=None,
            )
            prefs_changed = True

    # Re-render with updated skill preferences
    if prefs_changed:
        highlighted = get_highlighted_skills_for_display(
            conn, user_id, context="resume", context_id=resume_id
        )
        rendered = render_snapshot(conn, user_id, snapshot, print_output=False, highlighted_skills=highlighted)
        updated_json = json.dumps(snapshot, default=str)
        update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)
    if project_name is None:
        return get_resume_by_id(conn, user_id, resume_id)
    if scope is None:
        scope = "resume_only" 
    if scope not in ("resume_only", "global"):
        scope = "resume_only"
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
        # No field updates, just return existing (skill prefs may have changed)
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


def add_project_to_resume(
    conn, user_id: int, resume_id: int, project_summary_id: int
) -> Optional[Dict[str, Any]]:
    """Add a project to a resume snapshot. Returns updated resume or None."""
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None
    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        return None
    projects = snapshot.get("projects") or []
    existing_names = {p.get("project_name") for p in projects}
    summaries = load_project_summaries_by_ids(conn, user_id, [project_summary_id])
    if not summaries:
        return None
    snapshot_data = build_resume_snapshot_data(
        conn, user_id, summaries, print_output=False, resume_id=resume_id
    )
    if not snapshot_data:
        return None
    new_project = snapshot_data[0]["projects"][0]
    if new_project.get("project_name") in existing_names:
        return None
    projects.append(new_project)
    snapshot["projects"] = projects
    snapshot["aggregated_skills"] = recompute_aggregated_skills(projects)
    snapshot = enrich_snapshot_with_dates(conn, user_id, snapshot)
    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
    updated_json = json.dumps(snapshot, default=str)
    update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)
    return get_resume_by_id(conn, user_id, resume_id)
