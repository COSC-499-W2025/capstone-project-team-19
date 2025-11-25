"""
src/db/github_commit_timestamps.py

Queries for the table github_commit_timestamps
"""

import sqlite3
from typing import Optional
import json

def get_commit_timestamps(conn, user_id: int, project_name: str) -> List[str]:
    """
    Returns raw commit timestamps for duration & recency calculations.
    """
    rows = conn.execute("""
        SELECT commit_timestamp
        FROM github_commit_timestamps
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchall()

    return [r[0] for r in rows] if rows else []