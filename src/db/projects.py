"""
src/db/projects.py

Manages project-level database operations:
 - Storing and retrieving project classifications
 - Tracking uploaded files and configurations
 - Handling relationships between users and projects
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import json
import hashlib

from .deduplication import insert_project, insert_project_version
from .uploads import create_upload


def _get_or_create_project_key(conn: sqlite3.Connection, user_id: int, project_name: str | None) -> int:
    """Resolve project_key for display name; create project row if missing (e.g. config-only uploads)."""
    name = project_name or "default"
    pk = get_project_key(conn, user_id, name)
    if pk is not None:
        return int(pk)
    return insert_project(conn, user_id, name)


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
        # Store config files in config_files table (keyed by project_key)
        if f.get("file_type") == "config":
            project_key = _get_or_create_project_key(conn, user_id, f.get("project_name"))
            cur.execute("""
                INSERT INTO config_files (
                    user_id, project_key, file_name, file_path
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id,
                project_key,
                f.get("file_name"),
                f.get("file_path"),
            ))
        else:
            # Store regular files in files table (versioned only; version_key required)
            vk = f.get("version_key")
            if vk is None:
                continue  # skip rows without version_key
            cur.execute("""
                INSERT INTO files (
                    user_id, version_key, file_name, file_path, extension, file_type, size_bytes, created, modified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                int(vk),
                f.get("file_name"),
                f.get("file_path"),
                f.get("extension"),
                f.get("file_type"),
                f.get("size_bytes"),
                f.get("created"),
                f.get("modified"),
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


def get_latest_version_key(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    """Return the latest version_key for the given (user_id, project_name), or None."""
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        return None
    row = conn.execute(
        """
        SELECT version_key
        FROM project_versions
        WHERE project_key = ?
        ORDER BY version_key DESC
        LIMIT 1
        """,
        (pk,),
    ).fetchone()
    return int(row[0]) if row else None


def get_version_keys_for_project(conn: sqlite3.Connection, user_id: int, project_name: str) -> List[int]:
    """Return all version_key values for the given (user_id, project_name)."""
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        return []
    rows = conn.execute(
        "SELECT version_key FROM project_versions WHERE project_key = ? ORDER BY version_key DESC",
        (pk,),
    ).fetchall()
    return [int(r[0]) for r in rows]


def get_or_create_version_key_for_project(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    """
    Return the latest version_key for (user_id, project_name), or create project + one version if missing.
    Used by parse_zip_file when persisting without an upload flow (no version_key on files_info).
    """
    vk = get_latest_version_key(conn, user_id, project_name)
    if vk is not None:
        return vk
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        pk = insert_project(conn, user_id, project_name)
    vk = insert_project_version(conn, pk, None, f"{project_name}_parse_fp", f"{project_name}_parse_loose")
    conn.commit()
    return vk


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


def record_project_classification(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    project_name: str,
    classification: str,
    project_type: str | None = None,
    when: str | datetime | None = None,
) -> int:
    """
    Backwards-compatible helper (legacy name) to persist a project's classification.

    Historical schema used a `project_classifications` table and returned a `classification_id`.
    The schema now stores metadata on `projects` and keys metrics by `project_versions.version_key`.

    Returns:
        int: a `version_key` associated with this project (best-effort).
    """
    if classification is not None:
        _validate_classification(classification)
    if project_type is not None:
        _validate_project_type(project_type)

    # Ensure project exists
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        project_key = insert_project(conn, user_id, project_name)

    # Persist canonical metadata
    update_project_metadata(conn, project_key, classification=classification, project_type=project_type)

    # Prefer an existing version (normal CLI flow creates versions during dedup tagging)
    latest_vk = get_latest_version_key(conn, user_id, project_name)
    if latest_vk is not None:
        return latest_vk

    # Fallback for unit tests / isolated callers: create an upload + version row.
    upload_id = create_upload(conn, user_id, zip_name=zip_name, zip_path=zip_path, status="needs_classification")
    fp_seed = f"{user_id}|{project_key}|{zip_name}|{zip_path}"
    fp_strict = hashlib.sha256(fp_seed.encode("utf-8")).hexdigest()
    version_key = insert_project_version(
        conn,
        project_key=project_key,
        upload_id=upload_id,
        fingerprint_strict=fp_strict,
        fingerprint_loose=fp_strict,
    )

    # Optional: allow tests/callers to pin the version timestamp.
    if when is not None:
        if isinstance(when, datetime):
            when_val = when.isoformat()
        else:
            when_val = str(when)
        conn.execute(
            "UPDATE project_versions SET created_at = ? WHERE version_key = ?",
            (when_val, version_key),
        )

    conn.commit()
    return version_key


def record_project_classifications(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    assignments: dict[str, str],
) -> dict[str, int]:
    """
    Persist multiple project classifications for a single upload.

    Returns:
        Mapping of project_name -> version_key (best-effort).
    """
    version_keys: dict[str, int] = {}
    for project_name, classification in (assignments or {}).items():
        vk = record_project_classification(
            conn,
            user_id=user_id,
            zip_path=zip_path,
            zip_name=zip_name,
            project_name=project_name,
            classification=classification,
        )
        version_keys[project_name] = vk
    return version_keys


def get_classification_id(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    """
    Backwards-compatible name.
    Returns the latest `version_key` for this (user_id, project_name), or None.
    """
    return get_latest_version_key(conn, user_id, project_name)
