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
from src.services.resume_fit_service import compute_resume_fit_status
from src.db.skill_preferences import (
    has_skill_preferences,
    get_all_user_skills,
)
from src.db.user_profile import get_user_profile, get_contact_parts, get_visible_profile_text, get_resume_name
from src.db.user_education import list_user_education_entries
from src.db.user_experience import list_user_experience_entries
from src.db.users import get_user_by_id
from src.export.resume_helpers import filter_skills_by_highlighted
import json


def _clean_bullet_text(value: Any) -> str:
    # Keep behavior consistent with other parts of the app: trim and strip leading bullet markers.
    text = str(value).strip()
    if text.startswith(("-", "•")):
        text = text.lstrip("-•").strip()
    return text


def _validate_contribution_bullets(bullets: List[Any]) -> List[str]:
    MIN_BULLETS = 2
    MAX_BULLETS = 4
    MAX_BULLET_CHARS = 240

    cleaned: List[str] = [_clean_bullet_text(b) for b in bullets]
    cleaned = [b for b in cleaned if b]

    if len(cleaned) < MIN_BULLETS or len(cleaned) > MAX_BULLETS:
        raise ValueError(
            f"contribution_bullets must contain between {MIN_BULLETS} and {MAX_BULLETS} bullet points."
        )

    too_long = [i + 1 for i, b in enumerate(cleaned) if len(b) > MAX_BULLET_CHARS]
    if too_long:
        raise ValueError(
            f"Contribution bullet(s) {', '.join(map(str, too_long))} exceed {MAX_BULLET_CHARS} characters."
        )

    return cleaned


def list_user_resumes(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing resumes.
    """
    return list_resumes(conn, user_id)


def _get_username(conn, user_id: int) -> str:
    user = get_user_by_id(conn, user_id)
    if not user:
        return "user"
    if hasattr(user, "keys"):
        return str(user["username"])
    return str(user[1])


def _build_resume_preview(conn, user_id: int) -> Dict[str, Any]:
    profile = get_user_profile(conn, user_id)
    username = _get_username(conn, user_id)
    education_entries = list_user_education_entries(conn, user_id)
    experience_entries = list_user_experience_entries(conn, user_id)

    return {
        "display_name": get_resume_name(profile, username),
        "contact": get_contact_parts(profile),
        "profile_text": get_visible_profile_text(profile),
        "education_entries": [
            {
                "entry_id": entry["entry_id"],
                "entry_type": entry.get("entry_type"),
                "title": entry.get("title"),
                "organization": entry.get("organization"),
                "date_text": entry.get("date_text"),
                "description": entry.get("description"),
            }
            for entry in education_entries
            if entry.get("entry_type") == "education"
        ],
        "experience_entries": [
            {
                "entry_id": entry["entry_id"],
                "role": entry.get("role"),
                "company": entry.get("company"),
                "date_text": entry.get("date_text"),
                "description": entry.get("description"),
            }
            for entry in experience_entries
        ],
        "certificate_entries": [
            {
                "entry_id": entry["entry_id"],
                "entry_type": entry.get("entry_type"),
                "title": entry.get("title"),
                "organization": entry.get("organization"),
                "date_text": entry.get("date_text"),
                "description": entry.get("description"),
            }
            for entry in education_entries
            if entry.get("entry_type") == "certificate"
        ],
    }

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

    # Migrate legacy snapshots: add expertise tiers (Advanced / Intermediate / Beginner).
    # Only replace aggregated_skills when recompute actually finds skill data on projects;
    # otherwise keep stored technical/writing lists (minimal project stubs would yield empty).
    agg = snapshot.get("aggregated_skills") or {}
    if any(k not in agg for k in ("advanced", "intermediate", "beginner")):
        projects = snapshot.get("projects") or []
        if projects:
            recomputed = recompute_aggregated_skills(projects)
            has_recomputed_skills = bool(
                recomputed.get("technical_skills")
                or recomputed.get("writing_skills")
                or recomputed.get("advanced")
                or recomputed.get("intermediate")
                or recomputed.get("beginner")
            )
            if has_recomputed_skills:
                snapshot["aggregated_skills"] = recomputed
            else:
                merged = dict(agg)
                for k in ("advanced", "intermediate", "beginner"):
                    merged.setdefault(k, [])
                snapshot["aggregated_skills"] = merged
        else:
            merged = dict(agg)
            for k in ("advanced", "intermediate", "beginner"):
                merged.setdefault(k, [])
            snapshot["aggregated_skills"] = merged

    # Apply skill preference filtering only when this resume has its own explicit
    # preferences. Global preferences are intentionally excluded here so that a
    # newly-created resume always starts with all skills visible; global prefs
    # only affect exports and the portfolio view.
    if has_skill_preferences(conn, user_id, "resume", context_id=resume_id):
        highlighted = get_highlighted_skills_for_display(
            conn, user_id, context="resume", context_id=resume_id
        )
        agg = snapshot.get("aggregated_skills", {})
        agg["technical_skills"] = filter_skills_by_highlighted(agg.get("technical_skills", []), highlighted)
        agg["writing_skills"] = filter_skills_by_highlighted(agg.get("writing_skills", []), highlighted)
        for tier_key in ("advanced", "intermediate", "beginner"):
            agg[tier_key] = filter_skills_by_highlighted(agg.get(tier_key, []), highlighted)
        snapshot["aggregated_skills"] = agg
        for project in snapshot.get("projects", []):
            if "skills" in project:
                project["skills"] = filter_skills_by_highlighted(project["skills"], highlighted)

    # Resolve overrides so the API returns the effective values
    for project in snapshot.get("projects", []):
        project["project_name"] = resolve_resume_display_name(project)
        project["summary_text"] = resolve_resume_summary_text(project)
        project["contribution_bullets"] = resolve_resume_contribution_bullets(project)
        project["key_role"] = resolve_resume_key_role(project)

    one_page_status = compute_resume_fit_status(conn, user_id, record)

    # Combine DB fields with parsed JSON
    return {
        "id": record["id"],
        "name": record["name"],
        "created_at": record["created_at"],
        "rendered_text": record.get("rendered_text"),
        "one_page_status": one_page_status,
        "preview": _build_resume_preview(conn, user_id),
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
        # Validate user-provided bullets so exports don't need to truncate text.
        # Note: we validate the final bullet list after applying append/replace logic.
        if contribution_edit_mode == "append" and contribution_bullets:
            # Append new bullets to existing ones
            current_bullets = resolve_resume_contribution_bullets(project_entry)
            combined = current_bullets + contribution_bullets
            updates["contribution_bullets"] = _validate_contribution_bullets(combined)
        else:
            # Replace mode: use provided bullets directly
            updates["contribution_bullets"] = (
                _validate_contribution_bullets(contribution_bullets)
                if contribution_bullets
                else None
            )
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
    conn,
    user_id: int,
    resume_id: int,
    project_summary_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Add a single project to an existing resume snapshot.

    Returns the updated resume dict, or None if the resume/project could not be
    loaded or the project is already present in the resume.
    """
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        return None

    try:
        snapshot = json.loads(record["resume_json"])
    except json.JSONDecodeError:
        return None

    existing_projects = snapshot.get("projects") or []
    if any(
        p.get("project_summary_id") == project_summary_id
        for p in existing_projects
    ):
        return None

    summaries = load_project_summaries_by_ids(conn, user_id, [project_summary_id])
    if not summaries:
        return None

    new_snapshot_data = build_resume_snapshot_data(
        conn,
        user_id,
        summaries,
        print_output=False,
        resume_id=resume_id,
    )
    if not new_snapshot_data:
        return None

    new_snapshot, _rendered = new_snapshot_data
    new_projects = new_snapshot.get("projects") or []
    if not new_projects:
        return None

    new_project = new_projects[0]
    if any(p.get("project_name") == new_project.get("project_name") for p in existing_projects):
        return None

    snapshot["projects"] = [*existing_projects, new_project]
    snapshot["aggregated_skills"] = recompute_aggregated_skills(snapshot["projects"])
    snapshot = enrich_snapshot_with_dates(conn, user_id, snapshot)
    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
    updated_json = json.dumps(snapshot, default=str)
    update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)

    return get_resume_by_id(conn, user_id, resume_id)
