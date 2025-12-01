from __future__ import annotations

from typing import Any, Dict, List, Tuple
import json

from src.db import (
    get_text_duration,
    get_code_collaborative_duration,
    get_code_activity_percentages,
    get_code_collaborative_non_llm_summary,
)


def format_duration(
    project_type: str,
    project_mode: str,
    created_at: str,
    user_id: int,
    project_name: str,
    conn,
) -> str:
    """
    Build a simple 'Duration: start – end' (or single date / N/A) line.
    Priority:
    - text projects: use text_activity_contribution start/end via project_classifications
    - code(collaborative): use code_collaborative_metrics first/last commit
    """

    # 1) Text projects: use text_activity_contribution
    if project_type == "text":
        text_duration = get_text_duration(conn, user_id, project_name)
        if text_duration is not None:
            start, end = text_duration
            if start and end:
                return f"Duration: {start[:10]} – {end[:10]}"
            if start:
                return f"Duration: {start[:10]}"
            if end:
                return f"Duration: {end[:10]}"

    # 2) Collaborative code: use git first/last commit
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

    return "Duration: N/A"


def format_languages(summary: Dict[str, Any]) -> str:
    languages = summary.get("languages") or []
    if not languages:
        return "Languages: N/A"
    display = ", ".join(languages[:3])
    return f"Languages: {display}"


def format_frameworks(summary: Dict[str, Any]) -> str:
    frameworks = summary.get("frameworks") or []

    # If it's already a list of strings, good.
    if isinstance(frameworks, list):
        names = [str(f) for f in frameworks]

    # If it's a dict like {"React": {...}, "Express": {...}}, use the keys.
    elif isinstance(frameworks, dict):
        names = list(frameworks.keys())

    # If it's a set, turn into list.
    elif isinstance(frameworks, set):
        names = [str(f) for f in frameworks]

    # If it's a string, try to parse or fall back to comma-split.
    elif isinstance(frameworks, str):
        cleaned = frameworks.strip()
        parsed = None

        # Try JSON first: '["React", "Express"]'
        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = None

        if isinstance(parsed, list):
            names = [str(f) for f in parsed]
        else:
            # Fallback: "React, Express, Next.js"
            names = [part.strip() for part in cleaned.split(",") if part.strip()]

    else:
        names = []

    if not names:
        return "Frameworks: N/A"

    # Optional: sort + cap to avoid gigantic lines
    display = ", ".join(sorted(names)[:8])
    return f"Frameworks: {display}"


def _activity_from_json_text(summary: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    For text projects, compute activity percentages from JSON.
    Handles both:
    - collaborative text: contributions.activity_type
    - individual text:    metrics.activity_type
    """
    activity = None

    # 1) Collaborative text: contributions.activity_type
    contributions = summary.get("contributions") or {}
    activity = contributions.get("activity_type")

    # 2) Individual text: metrics.activity_type
    if not isinstance(activity, dict):
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


def format_activity_line(
    project_type: str,
    project_mode: str,
    conn,
    user_id: int,
    project_name: str,
    summary: Dict[str, Any],
) -> str:
    """
    Build 'Activity: feature_coding 98%, testing 2%' line.
    - Code: ONLY use code_activity_metrics (source='combined')
    - Text: use JSON-based activity percentages
    """
    activities: List[Tuple[str, float]] = []

    if project_type == "code":
        scope = project_mode or "individual"

        # Code activity ONLY from DB
        activities = get_code_activity_percentages(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            scope=scope,
            source="combined",
        )

        if not activities:
            return "Activity: N/A"

    elif project_type == "text":
        activities = _activity_from_json_text(summary)

        if not activities:
            return "Activity: N/A"

    else:
        return "Activity: N/A"

    # Only show top 2 categories
    top = activities[:2]
    parts = [f"{name} {percent:.0f}%" for (name, percent) in top]
    return "Activity: " + ", ".join(parts)


def format_skills_block(summary: Dict[str, Any]) -> List[str]:
    """
    Build a block:
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


def format_summary_block(
    project_type: str,
    project_mode: str,
    summary: Dict[str, Any],
    conn,
    user_id: int,
    project_name: str,
) -> List[str]:
    """
    Build summary lines:
    LLM:
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
