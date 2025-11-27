"""
src/db/project_summaries.py

Handles storage and retrieval of project summaries.
"""

import sqlite3
import json


def save_project_summary(conn, user_id, project_name, summary_json):
    """
    Inserts or replaces a summary for a project.
    
    Args:
        conn: SQLite connection
        user_id: User ID
        project_name: Project name
        summary_json: JSON string representing ProjectSummary.__dict__
    
    Uses INSERT OR REPLACE to avoid duplicates based on (user_id, project_name).
    """
    # Extract project_type and project_mode from the JSON if available
    try:
        summary_dict = json.loads(summary_json)
        project_type = summary_dict.get("project_type")
        project_mode = summary_dict.get("project_mode")
    except (json.JSONDecodeError, AttributeError):
        project_type = None
        project_mode = None
    
    conn.execute("""
        INSERT OR REPLACE INTO project_summaries (
            user_id,
            project_name,
            project_type,
            project_mode,
            summary_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, project_name, project_type, project_mode, summary_json))
    conn.commit()


def get_project_summaries_list(conn, user_id):
    """
    Retrieve a list of all project summaries for a user.
    """
    rows = conn.execute("""
        SELECT project_summary_id, project_name, project_type, project_mode, created_at
        FROM project_summaries
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    return [
        {
            "project_summary_id": row[0],
            "project_name": row[1],
            "project_type": row[2],
            "project_mode": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]


def get_project_summary_by_name(conn, user_id, project_name):
    """
    Retrieve a specific project summary by project name.
    """
    row = conn.execute("""
        SELECT project_summary_id, project_name, project_type, project_mode, summary_json, created_at
        FROM project_summaries
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchone()

    if not row:
        return None

    return {
        "project_summary_id": row[0],
        "project_name": row[1],
        "project_type": row[2],
        "project_mode": row[3],
        "summary_json": row[4],
        "created_at": row[5]
    }

def get_project_summaries(conn, user_id):
    cursor = conn.execute("""
        SELECT project_name, project_type, project_mode, summary_json, created_at
        FROM project_summaries
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()

    return [
        {
            "project_name": r[0],
            "project_type": r[1],
            "project_mode": r[2],
            "summary_json": r[3],
            "created_at": r[4]
        }
        for r in rows
    ]