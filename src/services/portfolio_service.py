from typing import Any, Dict, List, Optional, Set
import json
import logging

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_by_name, get_project_summary_row, update_project_summary_json
from src.services.resume_overrides import (
    update_project_manual_overrides,
    apply_manual_overrides_to_resumes,
)
from src.insights.portfolio import (
    format_duration,
    format_languages,
    format_frameworks,
    format_activity_line,
    format_skills_block,
    format_summary_block,
    resolve_portfolio_display_name,
    resolve_portfolio_summary_text,
    resolve_portfolio_contribution_bullets,
)

logger = logging.getLogger(__name__)


class CorruptProjectDataError(Exception):
    pass


def build_portfolio_data(
    conn,
    user_id: int,
) -> Optional[List[Dict[str, Any]]]:
    """
    Build structured portfolio project data from all ranked projects.
    Returns a list of project dicts, or None if no projects found.

    Shared by the API route and the CLI menu.
    """
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        return None

    projects: List[Dict[str, Any]] = []

    for project_name, score in project_scores:
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue

        summary = row["summary"] or {}
        project_type = row.get("project_type") or summary.get("project_type") or "unknown"
        project_mode = row.get("project_mode") or summary.get("project_mode") or "individual"
        created_at = row.get("created_at") or ""

        display_name = resolve_portfolio_display_name(summary, project_name)
        duration = format_duration(project_type, project_mode, created_at, user_id, project_name, conn)
        activity = format_activity_line(project_type, project_mode, conn, user_id, project_name, summary)
        summary_text = resolve_portfolio_summary_text(summary)
        contribution_bullets = resolve_portfolio_contribution_bullets(
            summary, project_type, project_mode, conn, user_id, project_name,
        )

        # Extract languages and frameworks as lists
        languages: List[str] = []
        if project_type == "code":
            raw_langs = summary.get("languages") or []
            if isinstance(raw_langs, list):
                languages = raw_langs[:3]

        frameworks_list: List[str] = []
        if project_type == "code":
            frameworks_line = format_frameworks(summary)
            if frameworks_line and not frameworks_line.endswith("N/A"):
                frameworks_list = [f.strip() for f in frameworks_line.replace("Frameworks: ", "").split(",") if f.strip()]

        # Extract skills as list
        skill_lines = format_skills_block(summary)
        skills: List[str] = []
        for line in skill_lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                skills.append(stripped[2:])

        projects.append({
            "project_name": project_name,
            "display_name": display_name,
            "project_type": project_type,
            "project_mode": project_mode,
            "score": round(score, 3),
            "duration": duration,
            "languages": languages,
            "frameworks": frameworks_list,
            "activity": activity,
            "skills": skills,
            "summary_text": summary_text,
            "contribution_bullets": contribution_bullets,
        })

    return projects if projects else None


def render_portfolio_text(
    name: str,
    projects: List[Dict[str, Any]],
    conn,
    user_id: int,
) -> str:
    """
    Build a plain-text rendered portfolio from structured project data.
    """
    lines: List[str] = []
    lines.append(f"Portfolio — {name}")
    lines.append("=" * 80)
    lines.append("")

    for rank, project in enumerate(projects, start=1):
        project_name = project["project_name"]
        row = get_project_summary_row(conn, user_id, project_name)
        summary = (row["summary"] or {}) if row else {}
        project_type = project["project_type"]
        project_mode = project["project_mode"]

        lines.append(f"[{rank}] {project['display_name']} — Score {project['score']:.3f}")
        lines.append(f"  Type: {project_type} ({project_mode})")
        lines.append(f"  {project['duration']}")
        if project_type == "code":
            lines.append(f"  {format_languages(summary)}")
            lines.append(f"  {format_frameworks(summary)}")
        lines.append(f"  {project['activity']}")
        for line in format_skills_block(summary):
            lines.append(f"  {line}")
        for line in format_summary_block(project_type, project_mode, summary, conn, user_id, project_name):
            lines.append(f"  {line}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def generate_portfolio(
    conn,
    user_id: int,
    name: str,
) -> Optional[Dict[str, Any]]:
    """
    Generate a portfolio view from all ranked projects.
    Returns a dict with 'projects' list and 'rendered_text', or None if no projects.
    """
    projects = build_portfolio_data(conn, user_id)
    if not projects:
        return None

    rendered_text = render_portfolio_text(name, projects, conn, user_id)

    return {
        "projects": projects,
        "rendered_text": rendered_text,
    }


def update_portfolio_overrides(
    conn,
    user_id: int,
    project_name: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Update portfolio-only overrides in project_summaries.summary_json.
    Shared by the API route and the CLI menu.
    """
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return None

    try:
        summary_dict = json.loads(summary_row["summary_json"])
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Corrupt summary_json for project '{project_name}': {e}")
        raise CorruptProjectDataError(f"Project '{project_name}' has corrupt data")

    overrides = summary_dict.get("portfolio_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    for key, value in updates.items():
        if value:
            overrides[key] = value
        else:
            overrides.pop(key, None)

    if overrides:
        summary_dict["portfolio_overrides"] = overrides
    else:
        summary_dict.pop("portfolio_overrides", None)

    updated = update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))
    if not updated:
        return None
    return overrides


def clear_portfolio_overrides_for_fields(
    conn,
    user_id: int,
    project_name: str,
    fields: Set[str],
) -> None:
    """
    Clear specific fields from portfolio_overrides so that manual_overrides take effect.
    Called when user makes a global edit from the portfolio flow.
    Shared by the API route and the CLI menu.
    """
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return

    try:
        summary_dict = json.loads(summary_row["summary_json"])
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Corrupt summary_json for project '{project_name}': {e}")
        raise CorruptProjectDataError(f"Project '{project_name}' has corrupt data")

    overrides = summary_dict.get("portfolio_overrides")
    if not overrides or not isinstance(overrides, dict):
        return

    changed = False
    for field in fields:
        if field in overrides:
            del overrides[field]
            changed = True

    if not changed:
        return

    if overrides:
        summary_dict["portfolio_overrides"] = overrides
    else:
        summary_dict.pop("portfolio_overrides", None)

    update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))


def edit_portfolio(
    conn,
    user_id: int,
    project_name: str,
    scope: str = "portfolio_only",
    display_name: Optional[str] = None,
    summary_text: Optional[str] = None,
    contribution_bullets: Optional[List[str]] = None,
    name: str = "Portfolio",
) -> Optional[Dict[str, Any]]:
    """
    Edit portfolio wording for a project.
    Returns the updated portfolio data, or None if project not found.
    """
    # Verify project exists
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
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
        # No field updates, return current portfolio
        return generate_portfolio(conn, user_id, name=name)

    if scope == "portfolio_only":
        result = update_portfolio_overrides(conn, user_id, project_name, updates)
        if result is None:
            return None
    else:
        # Global: update manual_overrides and fan out to resumes
        manual_overrides = update_project_manual_overrides(conn, user_id, project_name, updates)
        if manual_overrides is None:
            return None

        # Clear portfolio-specific overrides for these fields so global takes effect
        clear_portfolio_overrides_for_fields(conn, user_id, project_name, set(updates.keys()))

        apply_manual_overrides_to_resumes(
            conn,
            user_id,
            project_name,
            manual_overrides,
            set(updates.keys()),
        )

    return generate_portfolio(conn, user_id, name=name)
