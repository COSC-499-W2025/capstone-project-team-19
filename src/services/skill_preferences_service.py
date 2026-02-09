import sqlite3
from typing import List, Dict, Any, Optional, Literal

from src.db.skill_preferences import (
    get_user_skill_preferences,
    bulk_upsert_skill_preferences,
    clear_skill_preferences,
    get_all_user_skills,
    has_skill_preferences,
)
from src.db.skills import get_skill_events


def get_available_skills_with_status(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    # Get all skills from projects
    skill_events = get_skill_events(conn, user_id)

    # Aggregate skills: count projects and track max score
    skill_stats: Dict[str, Dict[str, Any]] = {}
    for row in skill_events:
        skill_name = row[0]
        score = row[2]

        if skill_name not in skill_stats:
            skill_stats[skill_name] = {
                "project_count": 0,
                "max_score": 0.0,
            }

        skill_stats[skill_name]["project_count"] += 1
        skill_stats[skill_name]["max_score"] = max(
            skill_stats[skill_name]["max_score"],
            score or 0.0
        )

    # Get current preferences
    preferences = get_user_skill_preferences(conn, user_id, context, context_id)
    pref_map = {p["skill_name"]: p for p in preferences}

    # Build result: merge stats with preferences
    result: List[Dict[str, Any]] = []

    for skill_name, stats in skill_stats.items():
        pref = pref_map.get(skill_name, {})

        # Default: highlighted if no preference set
        is_highlighted = pref.get("is_highlighted", True)
        display_order = pref.get("display_order")

        result.append({
            "skill_name": skill_name,
            "is_highlighted": is_highlighted,
            "display_order": display_order,
            "project_count": stats["project_count"],
            "max_score": round(stats["max_score"], 3),
        })

    # Sort by: display_order (if set), then by max_score descending
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
) -> List[Dict[str, Any]]:
    bulk_upsert_skill_preferences(
        conn=conn,
        user_id=user_id,
        preferences=skills,
        context=context,
        context_id=context_id,
    )

    return get_available_skills_with_status(conn, user_id, context, context_id)


def get_highlighted_skills_for_display(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    all_skills: Optional[List[str]] = None,
) -> List[str]:
    # Check if user has any preferences at all
    if not has_skill_preferences(conn, user_id, context, context_id):
        # Also check global fallback
        if context != "global" and not has_skill_preferences(conn, user_id, "global"):
            # No preferences at all - return all skills as-is
            if all_skills is not None:
                return all_skills
            return get_all_user_skills(conn, user_id)

    # Get all preferences (includes both highlighted and hidden skills)
    preferences = get_user_skill_preferences(conn, user_id, context, context_id)
    pref_map = {p["skill_name"]: p for p in preferences}

    # Get all user's skills from projects
    all_user_skills = get_all_user_skills(conn, user_id)

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
    for skill_name in all_user_skills:
        if skill_name not in pref_map and skill_name not in highlighted:
            highlighted.append(skill_name)

    if all_skills is not None:
        # Filter to only include skills that exist in all_skills
        return [s for s in highlighted if s in all_skills]

    return highlighted


def reset_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> int:
    return clear_skill_preferences(conn, user_id, context, context_id)


def copy_preferences_to_context(
    conn: sqlite3.Connection,
    user_id: int,
    from_context: Literal["global", "portfolio", "resume"] = "global",
    from_context_id: Optional[int] = None,
    to_context: Literal["global", "portfolio", "resume"] = "portfolio",
    to_context_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    source_prefs = get_user_skill_preferences(
        conn, user_id, from_context, from_context_id
    )

    if source_prefs:
        bulk_upsert_skill_preferences(
            conn=conn,
            user_id=user_id,
            preferences=source_prefs,
            context=to_context,
            context_id=to_context_id,
        )

    return get_available_skills_with_status(conn, user_id, to_context, to_context_id)
