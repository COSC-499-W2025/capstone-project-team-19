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
                    user_id, file_name, file_path, extension, file_type, size_bytes, created, modified, project_name, version_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                f.get("version_key"),
            ))
    
    conn.commit()


def _validate_classification(classification: str) -> None:
    if classification not in {"individual", "collaborative"}:
        raise ValueError("classification must be 'individual' or 'collaborative'")


def _validate_project_type(project_type: str) -> None:
    if project_type not in {"code", "text"}:
        raise ValueError("project_type must be 'code' or 'text'")


def update_project_metadata(
    conn: sqlite3.Connection,
    project_key: int,
    *,
    classification: str | None = None,
    project_type: str | None = None,
) -> None:
    """
    Update canonical project metadata in `projects`.
    Both fields are nullable (chosen later in the upload/analysis flow).
    """
    if classification is not None:
        _validate_classification(classification)
        conn.execute(
            "UPDATE projects SET classification = ? WHERE project_key = ?",
            (classification, project_key),
        )

    if project_type is not None:
        _validate_project_type(project_type)
        conn.execute(
            "UPDATE projects SET project_type = ? WHERE project_key = ?",
            (project_type, project_key),
        )

    conn.commit()


def get_project_key(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    """Best-effort lookup by display name (used by CLI paths)."""
    row = conn.execute(
        """
        SELECT project_key
        FROM projects
        WHERE user_id = ? AND display_name = ?
        ORDER BY project_key DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return int(row[0]) if row else None


def get_project_metadata(conn: sqlite3.Connection, user_id: int, project_name: str):
    """Returns (classification, project_type) from `projects` for the given display name."""
    row = conn.execute(
        """
        SELECT classification, project_type
        FROM projects
        WHERE user_id = ? AND display_name = ?
        ORDER BY project_key DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()

    if not row:
        return None, None
    return row[0], row[1]

def get_latest_version_key(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    """Return the most recent version_key for a project (by display_name)."""
    row = conn.execute(
        """
        SELECT pv.version_key
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = ? AND p.display_name = ?
        ORDER BY pv.version_key DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return int(row[0]) if row else None

def get_zip_name_for_project(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[str]:
    """
    Return the zip_name associated with the *latest* version of a project.
    (zip metadata lives in `uploads`, linked via `project_versions.upload_id`.)
    """
    row = conn.execute(
        """
        SELECT u.zip_name
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        JOIN uploads u ON u.upload_id = pv.upload_id
        WHERE p.user_id = ? AND p.display_name = ?
        ORDER BY pv.version_key DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row else None
