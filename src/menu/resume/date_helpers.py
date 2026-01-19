from src.db import get_text_duration, get_code_collaborative_duration, get_code_individual_duration

import sqlite3
from typing import Optional, Tuple, Dict, Any

def _best_project_duration(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    project_type: str | None,
    project_mode: str | None,
) -> Optional[Tuple[str | None, str | None]]:
    """
    Returns (start_date, end_date) or None.
    Uses your existing DB helpers.
    """
    if not conn or user_id is None or not project_name:
        return None

    if project_type == "code":
        if project_mode == "individual":
            return get_code_individual_duration(conn, user_id, project_name)
        if project_mode == "collaborative":
            return get_code_collaborative_duration(conn, user_id, project_name)

        # fallback if mode missing
        dur = get_code_individual_duration(conn, user_id, project_name)
        if dur:
            return dur
        return get_code_collaborative_duration(conn, user_id, project_name)

    # text projects
    return get_text_duration(conn, user_id, project_name)

def enrich_snapshot_with_dates(conn, user_id: int, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    projects = snapshot.get("projects") or []
    for p in projects:
        project_name = p.get("project_name") or ""
        project_type = p.get("project_type")
        project_mode = p.get("project_mode")

        dur = _best_project_duration(conn, user_id, project_name, project_type, project_mode)
        if dur:
            start_date, end_date = dur
            p["start_date"] = start_date
            p["end_date"] = end_date
        else:
            p["start_date"] = None
            p["end_date"] = None
    return snapshot
