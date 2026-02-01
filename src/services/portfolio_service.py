from typing import Any, Dict, List, Optional

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db.portfolio import (
    get_project_summary_row,
    get_code_activity_percentages,
    get_code_collaborative_duration,
    get_code_collaborative_non_llm_summary,
    get_text_duration,
    get_code_individual_duration,
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
        summary_text = _resolve_summary_text(summary, conn, user_id, project_name, project_type or "", project_mode or "")

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
            scope = (project_mode or "individual")
            percents = get_code_activity_percentages(conn, user_id, project_name, scope, "combined")
            if percents:
                activities = [{"name": name, "percent": round(pct, 2)} for name, pct in percents]
            else:
                activities = _extract_activities_from_summary(summary)

        items.append({
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
        })

    return items