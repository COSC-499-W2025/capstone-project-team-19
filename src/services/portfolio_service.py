from typing import Any, Dict, List, Optional

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_row
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
