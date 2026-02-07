"""
Database operations for the 'config_files' table.
Handles retrieval of config file metadata for projects.
"""

import sqlite3
from typing import List


def get_config_files_for_project(conn: sqlite3.Connection, user_id: int, project_key: int) -> List[str]:
    """
    Return a list of file paths for config files associated with the given user and project.
    """
    rows = conn.execute("""
        SELECT file_path
        FROM config_files
        WHERE user_id = ? AND project_key = ?
    """, (user_id, project_key)).fetchall()

    return [r[0] for r in rows if r and r[0]]
