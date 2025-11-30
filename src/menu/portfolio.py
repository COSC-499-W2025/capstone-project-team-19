# src/menu/portfolio.py
"""
Menu option for viewing portfolio items.
- Ordered by existing project importance scores
- One compact "card" per project
"""


from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import (
    get_project_summary_row,
    get_code_activity_percentages,
    get_code_collaborative_duration,
    get_code_collaborative_non_llm_summary,
)


def _format_duration(
    project_type: str,
    project_mode: str,
    created_at: str,
    user_id: int,
    project_name: str,
    conn,
) -> str:
    """
    Build a simple 'Duration: start – end' (or single date / N/A) line.

    For now:
    - code(collaborative): use code_collaborative_metrics first/last commit
    - other projects: fall back to created_at date
    """
    if project_type == "code" and project_mode == "collaborative":
        duration = get_code_collaborative_duration(conn, user_id, project_name)
        if duration is not None:
            first, last = duration
            if first and last:
                return f"Duration: {first[:10]} – {last[:10]}"
            if first:
                return f"Duration: {first[:10]}"
            if last:
                return f"Duration: {last[:10]}"

    if created_at:
        return f"Duration: {created_at[:10]}"

    return "Duration: N/A"


def _format_languages(summary: Dict[str, Any]) -> str:
    languages = summary.get("languages") or []
    if not languages:
        return "Languages: N/A"
    display = ", ".join(languages[:3])
    return f"Languages: {display}"


def _format_frameworks(summary: Dict[str, Any]) -> str:
    frameworks = summary.get("frameworks") or []
    if not frameworks:
        return "Frameworks: N/A"
    display = ", ".join(frameworks)
    return f"Frameworks: {display}"


def _activity_from_json_code(summary: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    Fallback: compute activity percentages from JSON if DB metrics are missing.
    Handles both:
    - code collaborative: contributions.activity_type
    - code individual:   metrics.activity_type
    """
    activity = None

    metrics = summary.get("metrics") or {}
    if "activity_type" in metrics:
        activity = metrics["activity_type"]

    if activity is None:
        contributions = summary.get("contributions") or {}
        activity = contributions.get("activity_type")

    if not isinstance(activity, dict):
        return []

    totals = 0
    for v in activity.values():
        try:
            totals += int(v.get("count", 0))
        except Exception:
            continue

    if totals <= 0:
        return []

    result: List[Tuple[str, float]] = []
    for name, v in activity.items():
        try:
            count = int(v.get("count", 0))
        except Exception:
            continue
        if count <= 0:
            continue
        percent = (count / totals) * 100.0
        result.append((name, percent))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _activity_from_json_text(summary: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    For text projects, use metrics.activity_type counts to compute percentages.
    """
    metrics = summary.get("metrics") or {}
    activity = metrics.get("activity_type")
    if not isinstance(activity, dict):
        return []

    total = 0
    for v in activity.values():
        try:
            total += int(v.get("count", 0))
        except Exception:
            continue

    if total <= 0:
        return []

    result: List[Tuple[str, float]] = []
    for name, v in activity.items():
        try:
            count = int(v.get("count", 0))
        except Exception:
            continue
        if count <= 0:
            continue
        percent = (count / total) * 100.0
        result.append((name, percent))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _format_activity_line(
    project_type: str,
    project_mode: str,
    conn,
    user_id: int,
    project_name: str,
    summary: Dict[str, Any],
) -> str:
    """
    Build 'Activity: feature_coding 98%, testing 2%' line.

    - For code: use code_activity_metrics (source='combined') if present,
      otherwise fall back to JSON.
    - For text: use JSON-based activity percentages.
    """
    activities: List[Tuple[str, float]] = []

    if project_type == "code":
        scope = project_mode or "individual"
        activities = get_code_activity_percentages(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            scope=scope,
            source="combined",
        )
        if not activities:
            activities = _activity_from_json_code(summary)

    elif project_type == "text":
        activities = _activity_from_json_text(summary)

    if not activities:
        return "Activity: N/A"

    top = activities[:2]
    parts = [f"{name} {percent:.0f}%" for (name, percent) in top]
    return "Activity: " + ", ".join(parts)


def _format_skills_block(summary: Dict[str, Any]) -> List[str]:
    """
    Build a block:

    Skills:
      - skill1
      - skill2
    """
    metrics = summary.get("metrics") or {}
    detailed = metrics.get("skills_detailed") or []
    skill_names: List[str] = []

    if isinstance(detailed, list) and detailed:
        try:
            sorted_skills = sorted(
                detailed,
                key=lambda s: float(s.get("score", 0.0)),
                reverse=True,
            )
        except Exception:
            sorted_skills = detailed

        for s in sorted_skills[:4]:
            name = s.get("skill_name")
            if isinstance(name, str):
                skill_names.append(name)

    if not skill_names:
        skills = summary.get("skills") or []
        if isinstance(skills, list):
            skill_names = skills[:4]

    if not skill_names:
        return ["Skills: N/A"]

    lines = ["Skills:"]
    for name in skill_names:
        lines.append(f"  - {name}")
    return lines


def _format_summary_block(
    project_type: str,
    project_mode: str,
    summary: Dict[str, Any],
    conn,
    user_id: int,
    project_name: str,
) -> List[str]:
    """
    Build summary lines:

    LLM-style:
      Summary:
        - Project: ...
        - My contribution: ...

    Non-LLM:
      Summary: <summary_text>
    """
    lines: List[str] = []
    project_summary = summary.get("summary_text") or ""
    contributions = summary.get("contributions") or {}

    # Code projects
    if project_type == "code":
        llm_contrib = contributions.get("llm_contribution_summary")
        if isinstance(llm_contrib, str) and llm_contrib.strip():
            lines.append("Summary:")
            lines.append(f"  - Project: {project_summary}")
            lines.append(f"  - My contribution: {llm_contrib}")
            return lines

        if project_mode == "collaborative":
            non_llm_content = get_code_collaborative_non_llm_summary(
                conn, user_id, project_name
            )
            if isinstance(non_llm_content, str) and non_llm_content.strip():
                lines.append(f"Summary: {non_llm_content}")
                return lines

        lines.append(f"Summary: {project_summary}")
        return lines

    # Text projects
    if project_type == "text":
        text_collab = contributions.get("text_collab") or {}
        text_contrib = text_collab.get("contribution_summary")
        if isinstance(text_contrib, str) and text_contrib.strip():
            lines.append("Summary:")
            lines.append(f"  - Project: {project_summary}")
            lines.append(f"  - My contribution: {text_contrib}")
            return lines

        lines.append(f"Summary: {project_summary}")
        return lines

    # Fallback
    lines.append(f"Summary: {project_summary}")
    return lines


def view_portfolio_items(conn, user_id: int, username: str):
    """
    Placeholder: Display items suitable for a portfolio.
    """
    # TODO: Implement portfolio items display
    return None