"""
src/db/drive_files.py

Google Drive file-related database operations:
 - Storing links between local files and Google Drive files
 - Retrieving Drive file information
"""

import sqlite3
from typing import Optional


def store_file_link(conn: sqlite3.Connection, user_id: int, project_name: str, local_file_name: str, drive_file_id: str, drive_file_name: Optional[str] = None, mime_type: Optional[str] = None, status: str = 'auto_matched') -> None:
    """
    Store a link between a local ZIP file and a Google Drive file.
    Status must be one of: 'auto_matched', 'manual_selected', 'not_found'
    
    Uses UNIQUE constraint to prevent duplicates: (user_id, project_name, local_file_name)
    """
    if status not in {'auto_matched', 'manual_selected', 'not_found'}:
        raise ValueError("status must be 'auto_matched', 'manual_selected', or 'not_found'")
    
    # Delete any existing entry for this file first (to ensure clean state)
    conn.execute("""
        DELETE FROM project_drive_files
        WHERE user_id=? AND project_name=? AND local_file_name=?
    """, (user_id, project_name, local_file_name))
    
    # Insert new entry
    conn.execute("""
        INSERT INTO project_drive_files (
            user_id, project_name, local_file_name, drive_file_id,
            drive_file_name, mime_type, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, project_name, local_file_name, drive_file_id, drive_file_name, mime_type, status))
    conn.commit()


def get_project_drive_files(conn: sqlite3.Connection, user_id: int, project_name: str) -> list[dict]:
    """
    Get all linked Drive files for a project.
    Returns list of dicts with keys: local_file_name, drive_file_id, drive_file_name, mime_type, status
    """
    rows = conn.execute("""
        SELECT local_file_name, drive_file_id, drive_file_name, mime_type, status
        FROM project_drive_files
        WHERE user_id=? AND project_name=?
        ORDER BY linked_at
    """, (user_id, project_name)).fetchall()
    
    return [
        {
            'local_file_name': row[0],
            'drive_file_id': row[1],
            'drive_file_name': row[2],
            'mime_type': row[3],
            'status': row[4]
        }
        for row in rows
    ]


def get_unlinked_project_files(conn: sqlite3.Connection, user_id: int, project_name: str) -> list[str]:
    """
    Get list of local file names that have status 'not_found' (couldn't be linked).
    """
    rows = conn.execute("""
        SELECT local_file_name
        FROM project_drive_files
        WHERE user_id=? AND project_name=? AND status='not_found'
        ORDER BY linked_at
    """, (user_id, project_name)).fetchall()
    
    return [row[0] for row in rows]