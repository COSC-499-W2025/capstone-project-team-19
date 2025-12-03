"""
src/db/projects.py

Manages project-level database operations:
 - Storing and retrieving project classifications
 - Tracking uploaded files and configurations
 - Handling relationships between users and projects
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict
import json

def store_parsed_files(conn: sqlite3.Connection, files_info: list[dict], user_id: int) -> None:
    """
    Insert parsed metadata into the 'files' table.
    Config files are inserted into 'config_files' instead.
    Each file is linked to the user.
    """

    if not files_info:
        return # nothing to insert
    
    cur = conn.cursor()
    for f in files_info:
        # Store config files in config_files table
        if f.get("file_type") == "config":
            cur.execute("""
                INSERT INTO config_files (
                    user_id, project_name, file_name, file_path
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id,
                f.get("project_name"),
                f.get("file_name"),
                f.get("file_path"),
            ))
        else:
            #Store regular files in files table
            cur.execute("""
                INSERT INTO files (
                    user_id, file_name, file_path, extension, file_type, size_bytes, created, modified, project_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                f.get("file_name"),
                f.get("file_path"),
                f.get("extension"),
                f.get("file_type"),
                f.get("size_bytes"),
                f.get("created"),
                f.get("modified"),
                f.get("project_name"),
            ))
    
    conn.commit()


def record_project_classification(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    project_name: str,
    classification: str,
    when: datetime | None = None
) -> None:
    """Persist a single project classification selection."""
    if classification not in {"individual", "collaborative"}:
        raise ValueError("classification must be 'individual' or 'collaborative'")

    timestamp = (when or datetime.now()).isoformat()
    conn.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, recorded_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, zip_name, project_name) DO UPDATE SET
            classification=excluded.classification,
            recorded_at=excluded.recorded_at
        """,
        (user_id, zip_path, zip_name, project_name, classification, timestamp),
    )
    conn.commit()


def record_project_classifications(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    assignments: Dict[str, str],
    when: datetime | None = None,
) -> None:
    """Bulk helper that stores classifications for multiple project names."""
    for project_name, classification in assignments.items():
        record_project_classification(
            conn,
            user_id,
            zip_path,
            zip_name,
            project_name,
            classification,
            when=when,
        )


def get_project_classifications(
    conn: sqlite3.Connection,
    user_id: int,
    zip_name: str,
) -> dict[str, str]:
    """Fetch saved classifications for a given user + uploaded ZIP."""
    rows = conn.execute(
        """
        SELECT project_name, classification
        FROM project_classifications
        WHERE user_id=? AND zip_name=?
        """,
        (user_id, zip_name),
    ).fetchall()
    return {project_name: classification for project_name, classification in rows}


def get_classification_id(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    row = conn.execute(
        """
        SELECT classification_id
        FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row else None

def get_project_metadata(conn, user_id, project_name):
    """
    Returns (classification, project_type) for a project.
    If nothing is found, returns (None, None).
    Reads the most recent entry from project_classifications.
    """
    row = conn.execute(
        """
        SELECT classification, project_type
        FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        ORDER BY recorded_at DESC
        LIMIT 1;
        """,
        (user_id, project_name)
    ).fetchone()

    if not row:
        return None, None

    return row[0], row[1]


def get_zip_name_for_project(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[str]:
    """
    Return the zip_name associated with a project for a given user.
    Uses the most recent classification record.
    """
    row = conn.execute(
        """
        SELECT zip_name
        FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row else None
