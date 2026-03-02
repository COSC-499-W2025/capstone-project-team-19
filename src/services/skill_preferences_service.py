import sqlite3
from typing import List, Dict, Any, Optional, Literal

from src.db.skill_preferences import (
    get_user_skill_preferences,
    bulk_upsert_skill_preferences,
    clear_skill_preferences,
    get_all_user_skills,
    get_project_skill_names,
    has_skill_preferences,
)
from src.db.skills import get_skill_events
from src.db.projects import get_project_key


def get_available_skills_with_status(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    project_key: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if project_key is not None:
        # Per-project: get skills only for this project
        cursor = conn.execute(
            "SELECT skill_name, level, score FROM project_skills WHERE user_id = ? AND project_key = ? AND score > 0 ORDER BY score DESC",
            (user_id, project_key)
        )
        skill_stats: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            skill_name, score = row[0], row[2]
            skill_stats[skill_name] = {"project_count": 1, "max_score": score or 0.0}
    else:
        # All projects: existing behavior
        skill_events = get_skill_events(conn, user_id)
        skill_stats = {}
        for row in skill_events:
            skill_name = row[0]
            score = row[2]
            if skill_name not in skill_stats:
                skill_stats[skill_name] = {"project_count": 0, "max_score": 0.0}
            skill_stats[skill_name]["project_count"] += 1
            skill_stats[skill_name]["max_score"] = max(
                skill_stats[skill_name]["max_score"], score or 0.0
            )

    # Get current preferences
    preferences = get_user_skill_preferences(conn, user_id, context, context_id, project_key)
    pref_map = {p["skill_name"]: p for p in preferences}

    # Build result: merge stats with preferences
    result: List[Dict[str, Any]] = []
    for skill_name, stats in skill_stats.items():
        pref = pref_map.get(skill_name, {})
        is_highlighted = pref.get("is_highlighted", True)
        display_order = pref.get("display_order")

        result.append({
            "skill_name": skill_name,
            "is_highlighted": is_highlighted,
            "display_order": display_order,
            "project_count": stats["project_count"],
            "max_score": round(stats["max_score"], 3),
        })

    result.sort(key=lambda x: (
        x["display_order"] if x["display_order"] is not None else 9999,
        -x["max_score"],
        x["skill_name"],
    ))

    return result


def update_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    skills: List[Dict[str, Any]],
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    project_key: Optional[int] = None,
) -> List[Dict[str, Any]]:
    bulk_upsert_skill_preferences(
        conn=conn,
        user_id=user_id,
        preferences=skills,
        context=context,
        context_id=context_id,
        project_key=project_key,
    )
    return get_available_skills_with_status(conn, user_id, context, context_id, project_key)


def get_highlighted_skills_for_display(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    project_key: Optional[int] = None,
    all_skills: Optional[List[str]] = None,
) -> List[str]:
    # Check if user has any preferences at all
    if not has_skill_preferences(conn, user_id, context, context_id, project_key):
        # Also check global fallback
        if context != "global" and not has_skill_preferences(conn, user_id, "global", project_key=project_key):
            # No preferences at all - return all skills as-is
            if all_skills is not None:
                return all_skills
            if project_key is not None:
                return get_project_skill_names(conn, user_id, project_key)
            return get_all_user_skills(conn, user_id)

    # Get all preferences (includes both highlighted and hidden skills)
    preferences = get_user_skill_preferences(conn, user_id, context, context_id, project_key)
    pref_map = {p["skill_name"]: p for p in preferences}

    # Get available skills (per-project or all)
    if project_key is not None:
        available_skills = get_project_skill_names(conn, user_id, project_key)
    else:
        available_skills = get_all_user_skills(conn, user_id)

    # Build result: skills are highlighted unless explicitly hidden in DB
    highlighted: List[str] = []

    # First add skills with explicit display_order (in order)
    ordered_prefs = sorted(
        [p for p in preferences if p["is_highlighted"] and p["display_order"] is not None],
        key=lambda p: p["display_order"]
    )
    for p in ordered_prefs:
        highlighted.append(p["skill_name"])

    # Then add highlighted skills without explicit order
    for p in preferences:
        if p["is_highlighted"] and p["display_order"] is None:
            if p["skill_name"] not in highlighted:
                highlighted.append(p["skill_name"])

    # Finally add skills NOT in preferences (default to highlighted)
    for skill_name in available_skills:
        if skill_name not in pref_map and skill_name not in highlighted:
            highlighted.append(skill_name)

    if all_skills is not None:
        return [s for s in highlighted if s in all_skills]

    return highlighted


def get_highlighted_skills_by_project(
    conn: sqlite3.Connection,
    user_id: int,
    project_names: List[str],
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> Dict[str, List[str]]:
    """Return a dict mapping project_name -> list of highlighted skill names."""
    result: Dict[str, List[str]] = {}
    for name in project_names:
        pk = get_project_key(conn, user_id, name)
        if pk is not None:
            result[name] = get_highlighted_skills_for_display(
                conn, user_id, context=context, context_id=context_id, project_key=pk
            )
        else:
            result[name] = []
    return result


def reset_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    project_key: Optional[int] = None,
) -> int:
    return clear_skill_preferences(conn, user_id, context, context_id, project_key)


def copy_preferences_to_context(
    conn: sqlite3.Connection,
    user_id: int,
    from_context: Literal["global", "portfolio", "resume"] = "global",
    from_context_id: Optional[int] = None,
    from_project_key: Optional[int] = None,
    to_context: Literal["global", "portfolio", "resume"] = "portfolio",
    to_context_id: Optional[int] = None,
    to_project_key: Optional[int] = None,
) -> List[Dict[str, Any]]:
    source_prefs = get_user_skill_preferences(
        conn, user_id, from_context, from_context_id, from_project_key
    )

    if source_prefs:
        bulk_upsert_skill_preferences(
            conn=conn,
            user_id=user_id,
            preferences=source_prefs,
            context=to_context,
            context_id=to_context_id,
            project_key=to_project_key,
        )

    return get_available_skills_with_status(conn, user_id, to_context, to_context_id, to_project_key)
