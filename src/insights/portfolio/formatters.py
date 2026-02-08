from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json
import re
from src.db import (
    get_text_duration,
    get_code_collaborative_duration,
    get_code_activity_percentages,
    get_code_collaborative_non_llm_summary,
    get_code_individual_duration,
)


def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _clean_bullets(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    for item in values:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith(("-", "•")):
            text = text.lstrip("-•").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _manual_overrides(summary: Dict[str, Any]) -> Dict[str, Any]:
    overrides = summary.get("manual_overrides") or {}
    if not isinstance(overrides, dict):
        return {}
    return overrides


def _portfolio_overrides(summary: Dict[str, Any]) -> Dict[str, Any]:
    overrides = summary.get("portfolio_overrides") or {}
    if not isinstance(overrides, dict):
        return {}
    return overrides


def resolve_portfolio_display_name(summary: Dict[str, Any], project_name: str) -> str:
    portfolio = _portfolio_overrides(summary)
    manual_name = _clean_str(portfolio.get("display_name"))
    if manual_name:
        return manual_name
    overrides = _manual_overrides(summary)
    manual_name = _clean_str(overrides.get("display_name"))
    return manual_name or project_name


def resolve_portfolio_summary_text(summary: Dict[str, Any]) -> str | None:
    portfolio = _portfolio_overrides(summary)
    manual_summary = _clean_str(portfolio.get("summary_text"))
    if manual_summary:
        return manual_summary
    overrides = _manual_overrides(summary)
    manual_summary = _clean_str(overrides.get("summary_text"))
    if manual_summary:
        return manual_summary
    return _clean_str(summary.get("summary_text"))


def resolve_portfolio_contribution_bullets(
    summary: Dict[str, Any],
    project_type: str,
    project_mode: str,
    conn,
    user_id: int,
    project_name: str,
) -> List[str]:
    portfolio = _portfolio_overrides(summary)
    bullets = _clean_bullets(portfolio.get("contribution_bullets"))
    if bullets:
        return bullets

    overrides = _manual_overrides(summary)
    bullets = _clean_bullets(overrides.get("contribution_bullets"))
    if bullets:
        return bullets

    contributions = summary.get("contributions") or {}
    if project_type == "code":
        manual_contrib = contributions.get("manual_contribution_summary") or contributions.get(
            "non_llm_contribution_summary"
        )
        if isinstance(manual_contrib, str) and manual_contrib.strip():
            return [manual_contrib.strip()]

        llm_contrib = contributions.get("llm_contribution_summary")
        if isinstance(llm_contrib, str) and llm_contrib.strip():
            return [llm_contrib.strip()]

        if project_mode == "collaborative" and conn and user_id is not None and project_name:
            non_llm_content = get_code_collaborative_non_llm_summary(conn, user_id, project_name)
            if isinstance(non_llm_content, str) and non_llm_content.strip():
                return [non_llm_content.strip()]

        return []

    if project_type == "text":
        text_collab = contributions.get("text_collab") or {}
        text_contrib = text_collab.get("contribution_summary")
        if isinstance(text_contrib, str) and text_contrib.strip():
            return [text_contrib.strip()]

    return []

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
    - code(individual):   use git_individual_metrics first/last commit
    """

    # 1) Text projects
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

    # 2) Collaborative code
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

    # 3) Individual code
    if project_type == "code" and (project_mode == "individual" or not project_mode):
        duration = get_code_individual_duration(conn, user_id, project_name)
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

    # CASE 1 — Already a list
    if isinstance(frameworks, list):
        cleaned = [str(f).strip() for f in frameworks if str(f).strip()]
        if cleaned:
            return f"Frameworks: {', '.join(cleaned)}"
        return "Frameworks: N/A"

    # CASE 2 — Already a dict (use keys)
    if isinstance(frameworks, dict):
        keys = [str(k).strip() for k in frameworks.keys()]
        if keys:
            return f"Frameworks: {', '.join(keys)}"
        return "Frameworks: N/A"

    # CASE 3 — A Python set/string like:
    #   "{'AVA', 'Axios', 'Babel'}"
    #   "{'AVA', 'Axios'}, 'Electron'"
    if isinstance(frameworks, str):
        s = frameworks.strip()

        # Remove surrounding braces if present
        s = re.sub(r'^\{|\}$', '', s).strip()

        # Remove single quotes
        s = s.replace("'", "")

        # Now split by comma
        parts = [p.strip() for p in s.split(",") if p.strip()]

        if parts:
            return f"Frameworks: {', '.join(parts)}"

        return "Frameworks: N/A"

    # Unknown type
    return "Frameworks: N/A"


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


def format_skills_block(summary: Dict[str, Any], highlighted_skills: List[str] | None = None,) -> List[str]:
    """
    Build a block:
      - skill1
      - skill2
    """
    metrics = summary.get("metrics") or {}
    detailed = metrics.get("skills_detailed") or []
    all_skill_names: List[str] = []

    if isinstance(detailed, list) and detailed:
        try:
            sorted_skills = sorted(
                detailed,
                key=lambda s: float(s.get("score", 0.0)),
                reverse=True,
            )
        except Exception:
            sorted_skills = detailed

        for s in sorted_skills:
            name = s.get("skill_name")
            if isinstance(name, str):
                all_skill_names.append(name)

    if not all_skill_names:
        skills = summary.get("skills") or []
        if isinstance(skills, list):
            all_skill_names = list(skills)

    if not all_skill_names:
        return ["Skills: N/A"]

    if highlighted_skills is not None:
        # Filter to only include highlighted skills, maintain highlighted order
        skill_names = [s for s in highlighted_skills if s in all_skill_names]
        # Limit to 4 skills for display
        skill_names = skill_names[:4]
    else:
        # Default: top 4 by score
        skill_names = all_skill_names[:4]

    if not skill_names:
        return ["Skills: N/A"]

    lines = ["Skills:"]
    for name in skill_names:
        lines.append(f"  - {name}")
    return lines


def get_all_skills_from_summary(summary: Dict[str, Any]) -> List[str]:
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

        for s in sorted_skills:
            name = s.get("skill_name")
            if isinstance(name, str):
                skill_names.append(name)

    if not skill_names:
        skills = summary.get("skills") or []
        if isinstance(skills, list):
            skill_names = list(skills)

    return skill_names


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
    portfolio = _portfolio_overrides(summary)
    manual = _manual_overrides(summary)
    project_summary = (
        _clean_str(portfolio.get("summary_text"))
        or _clean_str(manual.get("summary_text"))
        or summary.get("summary_text")
        or ""
    )
    contributions = summary.get("contributions") or {}
    manual_bullets = _clean_bullets(portfolio.get("contribution_bullets"))
    if not manual_bullets:
        manual_bullets = _clean_bullets(manual.get("contribution_bullets"))

    if manual_bullets:
        lines.append("Summary:")
        lines.append(f"  - Project: {project_summary}")
        if len(manual_bullets) == 1:
            lines.append(f"  - My contribution: {manual_bullets[0]}")
        else:
            lines.append("  My contributions:")
            for bullet in manual_bullets:
                lines.append(f"    - {bullet}")
        return lines

    # Code projects
    if project_type == "code":
        manual_contrib = contributions.get("manual_contribution_summary") or contributions.get(
            "non_llm_contribution_summary"
        )
        if isinstance(manual_contrib, str) and manual_contrib.strip():
            lines.append("Summary:")
            lines.append(f"  - Project: {project_summary}")
            lines.append(f"  - My contribution: {manual_contrib}")
            return lines

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
