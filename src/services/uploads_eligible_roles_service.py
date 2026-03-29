from __future__ import annotations

import sqlite3
from fastapi import HTTPException

from src.db.uploads import get_upload_by_id
from src.analysis.skills.roles.role_eligibility import get_eligible_roles


def get_eligible_roles_for_project(
    conn: sqlite3.Connection,
    user_id: int,
    upload_id: int,
    project_name: str,
) -> list[str]:
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    state = upload.get("state") or {}

    # Resolve project type from state
    project_type = (
        (state.get("project_types_manual") or {}).get(project_name)
        or (state.get("project_types_auto") or {}).get(project_name)
    )
    if project_type not in {"code", "text"}:
        raise HTTPException(status_code=409, detail="Project type not resolved for this project")

    # Try to load existing bucket scores from project_skills table
    # Scores exist if a previous version of this project was already analyzed
    bucket_scores = _load_bucket_scores(conn, user_id, project_name)

    return get_eligible_roles(project_type, bucket_scores)


def _load_bucket_scores(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> dict[str, float] | None:
    try:
        rows = conn.execute(
            """
            SELECT skill_name, score
            FROM project_skills
            WHERE user_id = ? AND project_name = ?
            """,
            (user_id, project_name),
        ).fetchall()
    except Exception:
        return None

    if not rows:
        return None

    return {row[0]: float(row[1]) for row in rows if row[1] is not None}