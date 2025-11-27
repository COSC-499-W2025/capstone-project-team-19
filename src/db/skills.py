"""
src/db/skills.py

Manages skill-metric database operations:
 - Storing and retrieving skills
"""

import sqlite3
from typing import List


def insert_project_skill(conn, user_id, project_name, skill_name, level, score, evidence):
    """
    Insert or update a skill entry for a project.
    Ensures only one row per (user_id, project_name, skill_name).
    """

    conn.execute(
        """
        INSERT INTO project_skills (user_id, project_name, skill_name, level, score, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, skill_name)
        DO UPDATE SET
            level = excluded.level,
            score = excluded.score,
            evidence_json = excluded.evidence_json
        ;
        """,
        (user_id, project_name, skill_name, level, score, evidence)
    )

def get_project_skills(conn, user_id: int, project_name: str) -> List[dict]:
    """
    Returns:
    - skill_name
    - level ("beginner"/"intermediate"/"advanced")
    - score (numeric)
    """
    rows = conn.execute("""
        SELECT skill_name, level, score
        FROM project_skills
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchall()

    return [
        {"skill": r[0], "level": r[1], "score": r[2]}
        for r in rows
    ] if rows else []