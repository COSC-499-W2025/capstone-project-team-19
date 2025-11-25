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

def get_project_summaries(conn, user_id):
    cursor = conn.execute("""
        SELECT *
        FROM project_summaries
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()
    return rows
