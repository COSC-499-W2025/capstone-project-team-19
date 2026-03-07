import json
import logging
from typing import Any, Dict, List, Optional, Set

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import (
    get_project_summary_row,
    get_code_activity_percentages,
    get_code_collaborative_duration,
    get_code_collaborative_non_llm_summary,
    get_text_duration,
    get_code_individual_duration,
    get_project_summary_by_name,
    update_project_summary_json,
)
from src.services.resume_overrides import (
    update_project_manual_overrides,
    apply_manual_overrides_to_resumes,
)
from src.services.skill_preferences_service import (
    get_highlighted_skills_for_display,
    update_skill_preferences,
    reset_skill_preferences,
    normalize_skill_preferences,
)
from src.db.skill_preferences import get_project_skill_names
from src.db.projects import get_project_key
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
    get_all_skills_from_summary,
)



def _normalize_frameworks(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(f).strip() for f in raw if str(f).strip()]
    if isinstance(raw, dict):
        return [str(k).strip() for k in raw if str(k).strip()]
    if isinstance(raw, str):
        s = raw.strip().replace("'", "")
        return [p.strip() for p in s.split(",") if p.strip()]
    return []


def _extract_skills(summary: Dict[str, Any]) -> List[str]:
    detailed = (summary.get("metrics") or {}).get("skills_detailed")
    if isinstance(detailed, list):
        names = [s.get("skill_name") for s in detailed if isinstance(s, dict) and s.get("skill_name")]
        return list(dict.fromkeys(names))
    skills = summary.get("skills")
    return list(skills) if isinstance(skills, list) else []


def _extract_activities_from_summary(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    activity = (summary.get("contributions") or {}).get("activity_type") or (summary.get("metrics") or {}).get("activity_type")
    if not isinstance(activity, dict):
        return []
    return [{"name": k, "top_file": v.get("top_file") or v.get("top_file_overall")} for k, v in activity.items()]


def _resolve_display_name(summary: Dict[str, Any], project_name: str) -> str:
    overrides = summary.get("manual_overrides") or {}
    name = (overrides.get("display_name") or "").strip()
    return name or project_name


def _resolve_summary_text(summary: Dict[str, Any], conn, user_id: int, project_name: str, project_type: str, project_mode: str) -> Optional[str]:
    overrides = summary.get("manual_overrides") or {}
    text = (overrides.get("summary_text") or summary.get("summary_text") or "").strip()
    if text:
        return text
    if project_type == "code" and project_mode == "collaborative":
        return get_code_collaborative_non_llm_summary(conn, user_id, project_name)
    return None


def _get_dates(conn, user_id: int, project_name: str, project_type: Optional[str], project_mode: Optional[str]):
    if project_type == "text":
        pair = get_text_duration(conn, user_id, project_name)
        return (pair[0], pair[1]) if pair else (None, None)
    if project_type == "code" and project_mode == "collaborative":
        pair = get_code_collaborative_duration(conn, user_id, project_name)
        return (pair[0], pair[1]) if pair else (None, None)
    if project_type == "code":
        pair = get_code_individual_duration(conn, user_id, project_name)
        return (pair[0], pair[1]) if pair else (None, None)
    return (None, None)

  
  
def get_portfolio(conn, user_id: int) -> List[Dict[str, Any]]:
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        return []

    items: List[Dict[str, Any]] = []
    for rank, (project_name, score) in enumerate(project_scores, start=1):
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue

        summary = row["summary"]
        project_type = row.get("project_type") or summary.get("project_type")
        project_mode = row.get("project_mode") or summary.get("project_mode")

        display_name = _resolve_display_name(summary, project_name)
        start_date, end_date = _get_dates(conn, user_id, project_name, project_type, project_mode)
        languages = list(summary.get("languages") or [])
        frameworks = _normalize_frameworks(summary.get("frameworks"))
        skills = _extract_skills(summary)
        summary_text = _resolve_summary_text(
            summary, conn, user_id, project_name, project_type or "", project_mode or ""
        )

        text_type: Optional[str] = None
        contribution_percent: Optional[float] = None
        if project_type == "text":
            text_type = "Academic writing"
            if project_mode == "collaborative":
                text_collab = (summary.get("contributions") or {}).get("text_collab")
                if isinstance(text_collab, dict):
                    pct = text_collab.get("percent_of_document")
                    if isinstance(pct, (int, float)):
                        contribution_percent = float(pct)

        activities: List[Dict[str, Any]] = []
        if project_type == "code":
            scope = project_mode or "individual"
            percents = get_code_activity_percentages(conn, user_id, project_name, scope, "combined")
            if percents:
                activities = [{"name": name, "percent": round(pct, 2)} for name, pct in percents]
            else:
                activities = _extract_activities_from_summary(summary)

        items.append(
            {
                "rank": rank,
                "project_name": project_name,
                "display_name": display_name,
                "score": round(score, 3),
                "project_type": project_type,
                "project_mode": project_mode,
                "start_date": start_date[:10] if start_date else None,
                "end_date": end_date[:10] if end_date else None,
                "languages": languages,
                "frameworks": frameworks,
                "summary_text": summary_text or None,
                "skills": skills,
                "text_type": text_type,
                "contribution_percent": contribution_percent,
                "activities": activities,
            }
        )

    return items


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
    Respects user skill highlighting preferences for portfolio context.

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

        # Extract skills as list, filtered by per-project user preferences
        all_project_skills = get_all_skills_from_summary(summary)

        pk = get_project_key(conn, user_id, project_name)
        highlighted_skills = get_highlighted_skills_for_display(
            conn=conn, user_id=user_id, context="portfolio", project_key=pk,
        ) if pk else None

        if highlighted_skills:
            skills = [s for s in highlighted_skills if s in all_project_skills][:4]
        else:
            skills = all_project_skills[:4]

        projects.append({
            "project_summary_id": row.get("project_summary_id"),
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
    Respects per-project skill highlighting preferences.
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

        # Get per-project highlighted skills
        pk = get_project_key(conn, user_id, project_name)
        highlighted_skills = get_highlighted_skills_for_display(
            conn=conn, user_id=user_id, context="portfolio", project_key=pk,
        ) if pk else None

        for line in format_skills_block(summary, highlighted_skills if highlighted_skills else None):
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
    skill_preferences: Optional[List[Dict[str, Any]]] = None,
    skill_preferences_reset: Optional[bool] = False,
) -> Optional[Dict[str, Any]]:
    """
    Edit portfolio wording for a project.
    Returns the updated portfolio data, or None if project not found.
    """
    # Verify project exists
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return None

    if scope not in ("portfolio_only", "global"):
        scope = "portfolio_only"

    pref_context = "portfolio" if scope == "portfolio_only" else "global"
    pref_context_id = None
    if skill_preferences_reset:
        project_key = get_project_key(conn, user_id, project_name)
        if project_key is None:
            return None
        reset_skill_preferences(
            conn,
            user_id,
            context=pref_context,
            context_id=pref_context_id,
            project_key=project_key,
        )
    elif skill_preferences:
        project_key = get_project_key(conn, user_id, project_name)
        if project_key is None:
            return None
        normalized_prefs = normalize_skill_preferences(skill_preferences)
        if normalized_prefs:
            valid_skills = set(get_project_skill_names(conn, user_id, project_key))
            invalid = [p["skill_name"] for p in normalized_prefs if p["skill_name"] not in valid_skills]
            if invalid:
                raise ValueError(f"Invalid skill name(s): {', '.join(invalid)}")
            update_skill_preferences(
                conn,
                user_id,
                normalized_prefs,
                context=pref_context,
                context_id=pref_context_id,
                project_key=project_key,
            )
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

