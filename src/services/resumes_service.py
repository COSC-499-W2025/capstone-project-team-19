from typing import List, Dict, Any, Optional, Literal
from src.db.resumes import list_resumes, get_resume_snapshot, insert_resume_snapshot, update_resume_snapshot
from src.db.project_summaries import get_project_summary_by_id, get_project_summary_by_name, update_project_summary_json
from src.db import get_all_user_project_summaries
from src.models.project_summary import ProjectSummary
from src.menu.resume.helpers import (
    build_resume_snapshot,
    render_snapshot,
    enrich_snapshot_with_contributions,
    apply_resume_only_updates,
    resume_only_override_fields,
)
from src.insights.rank_projects.rank_project_importance import collect_project_data
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
    summaries: List[ProjectSummary] = []

    if project_ids:
        # Fetch project summaries by IDs
        for project_id in project_ids:
            row = get_project_summary_by_id(conn, user_id, project_id)
            if row and row.get("summary_json"):
                try:
                    summary_dict = json.loads(row["summary_json"])
                    summaries.append(ProjectSummary.from_dict(summary_dict))
                except (json.JSONDecodeError, Exception):
                    continue
    else:
        # No project_ids provided - use top 5 ranked projects (like menu flow)
        ranked = collect_project_data(conn, user_id)
        if not ranked:
            return None

        top_names = [proj_name for proj_name, _score in ranked[:5]]

        # Load all summaries and filter to top ranked
        all_rows = get_all_user_project_summaries(conn, user_id)
        for row in all_rows:
            if row["project_name"] in top_names:
                try:
                    summary_dict = json.loads(row["summary_json"])
                    summaries.append(ProjectSummary.from_dict(summary_dict))
                except (json.JSONDecodeError, Exception):
                    continue

        # Sort by ranking order
        ranked_dict = {proj_name: score for proj_name, score in ranked}
        summaries.sort(key=lambda s: ranked_dict.get(s.project_name, 0.0), reverse=True)

    if not summaries:
        return None

    # Build snapshot (extracts projects and aggregates skills)
    snapshot = build_resume_snapshot(summaries)

    # Enrich with contribution bullets and dates
    snapshot = enrich_snapshot_with_contributions(conn, user_id, snapshot)

    # Render to text
    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)

    # Store in DB
    resume_json = json.dumps(snapshot, default=str)
    resume_id = insert_resume_snapshot(conn, user_id, name, resume_json, rendered)
    return get_resume_by_id(conn, user_id, resume_id)

def edit_resume(
    conn,
    user_id: int,
    resume_id: int,
    project_name: str,
    scope: Literal["resume_only", "global"],
    name: Optional[str] = None,
    display_name: Optional[str] = None,
    summary_text: Optional[str] = None,
    contribution_bullets: Optional[List[str]] = None,
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
        updates["contribution_bullets"] = contribution_bullets or None

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
        manual_overrides = _update_project_manual_overrides(conn, user_id, project_name, updates)
        if manual_overrides is not None:
            _apply_manual_overrides_to_resumes(
                conn,
                user_id,
                project_name,
                manual_overrides,
                set(updates.keys()),
                force_resume_id=resume_id,
            )

    return get_resume_by_id(conn, user_id, resume_id)


def _update_project_manual_overrides(
    conn,
    user_id: int,
    project_name: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update manual overrides in project_summaries table."""
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return None

    try:
        summary_dict = json.loads(summary_row["summary_json"])
    except Exception:
        return None

    overrides = summary_dict.get("manual_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    for key, value in updates.items():
        if value:
            overrides[key] = value
        else:
            overrides.pop(key, None)

    if overrides:
        summary_dict["manual_overrides"] = overrides
    else:
        summary_dict.pop("manual_overrides", None)

    updated = update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))
    if not updated:
        return None
    return overrides


def _apply_manual_overrides_to_resumes(
    conn,
    user_id: int,
    project_name: str,
    overrides: Dict[str, Any],
    fields: set,
    force_resume_id: Optional[int] = None,
) -> None:
    """Apply global overrides to all saved resumes containing this project."""
    resumes = list_resumes(conn, user_id)

    for r in resumes:
        record = get_resume_snapshot(conn, user_id, r["id"])
        if not record:
            continue
        try:
            snapshot = json.loads(record["resume_json"])
        except Exception:
            continue

        projects = snapshot.get("projects") or []
        changed = False

        for entry in projects:
            if entry.get("project_name") != project_name:
                continue

            resume_only_fields = resume_only_override_fields(entry)
            force_update = force_resume_id == r["id"]

            # If this is the selected resume, clear resume-only overrides so global applies
            if force_update and resume_only_fields:
                clear_updates = {field: None for field in fields}
                apply_resume_only_updates(entry, clear_updates)
                resume_only_fields = resume_only_override_fields(entry)

            if "display_name" in fields:
                if "display_name" not in resume_only_fields or force_update:
                    if overrides.get("display_name"):
                        entry["manual_display_name"] = overrides["display_name"]
                    else:
                        entry.pop("manual_display_name", None)
                    changed = True

            if "summary_text" in fields:
                if "summary_text" not in resume_only_fields or force_update:
                    if overrides.get("summary_text"):
                        entry["manual_summary_text"] = overrides["summary_text"]
                    else:
                        entry.pop("manual_summary_text", None)
                    changed = True

            if "contribution_bullets" in fields:
                if "contribution_bullets" not in resume_only_fields or force_update:
                    if overrides.get("contribution_bullets"):
                        entry["manual_contribution_bullets"] = overrides["contribution_bullets"]
                    else:
                        entry.pop("manual_contribution_bullets", None)
                    changed = True

        if changed:
            rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
            updated_json = json.dumps(snapshot, default=str)
            update_resume_snapshot(conn, user_id, r["id"], updated_json, rendered)