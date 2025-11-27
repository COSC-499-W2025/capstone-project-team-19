"""
src/db/skills.py

Manages skill-metric database operations:
 - Storing and retrieving skills
"""

import sqlite3
import json
from typing import List, Dict, Any


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


def get_project_skills(conn, user_id, project_name):
    """
    Retrieve all skills for a project with their details.
    Returns list of tuples: (skill_name, level, score, evidence_json)
    """
    cursor = conn.execute(
        """
        SELECT skill_name, level, score, evidence_json
        FROM project_skills
        WHERE user_id = ? AND project_name = ?
        ORDER BY score DESC
        """,
        (user_id, project_name)
    )
    
    return cursor.fetchall()
