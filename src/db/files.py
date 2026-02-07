"""
src/db/files.py

User-uploaded file database operations.
Files are versioned only: query by version_key (resolve project_name -> version_key via projects.py).
"""

import sqlite3
from typing import List, Tuple, Optional

from .projects import get_latest_version_key, get_version_keys_for_project


def get_files_for_user(conn: sqlite3.Connection, user_id: int) -> List[Tuple[str, str]]:
    """
    Return all (project_display_name, file_type) pairs for files that belong to a given user.
    Derives project name via files -> project_versions -> projects.
    """
    rows = conn.execute("""
        SELECT DISTINCT p.display_name, f.file_type
        FROM files f
        JOIN project_versions pv ON f.version_key = pv.version_key
        JOIN projects p ON pv.project_key = p.project_key
        WHERE f.user_id = ?
    """, (user_id,)).fetchall()
    return rows


def get_recent_file_paths_for_project(conn, user_id: int, project_name: str, limit: int = 200):
    """
    Return up to `limit` file paths for a given user + project_name (latest version),
    ordered by modified timestamp (newest first).
    """
    vk = get_latest_version_key(conn, user_id, project_name)
    if vk is None:
        return []
    rows = conn.execute("""
        SELECT DISTINCT file_path
        FROM files
        WHERE user_id = ? AND version_key = ?
        ORDER BY modified DESC
        LIMIT ?
    """, (user_id, vk, limit)).fetchall()
    return [r[0] for r in rows if r and r[0]]


def get_code_files_for_project(conn, user_id: int, project_name: str):
    """
    Return all (file_name, file_path) pairs for code files
    belonging to a user + project_name (latest version).
    """
    vk = get_latest_version_key(conn, user_id, project_name)
    if vk is None:
        return []
    rows = conn.execute("""
        SELECT file_name, file_path
        FROM files
        WHERE user_id = ? AND version_key = ? AND file_type = 'code'
    """, (user_id, vk)).fetchall()
    return rows


def get_files_for_project(conn, user_id: int, project_name: str, only_text: bool = False):
    """
    Return a list of dicts with file metadata for a given project (latest version):
        [{'file_name', 'file_type', 'file_path'}, ...]
    """
    vk = get_latest_version_key(conn, user_id, project_name)
    if vk is None:
        return []
    query = """
        SELECT file_name, file_type, file_path
        FROM files
        WHERE user_id = ? AND version_key = ?
    """
    params: list = [user_id, vk]
    if only_text:
        query += " AND file_type = 'text'"
    rows = conn.execute(query, params).fetchall()
    return [
        {"file_name": r[0], "file_type": r[1], "file_path": r[2]}
        for r in rows
    ]


def get_file_extension_by_path(conn, user_id: int, file_path: str):
    """
    Return the extension for an exact file_path match in the files table.
    """
    row = conn.execute("""
        SELECT extension
        FROM files
        WHERE user_id = ? AND file_path = ?
    """, (user_id, file_path)).fetchone()
    return row[0] if row else None


def find_file_extension_by_basename(conn, user_id: int, basename: str):
    """
    Fallback fuzzy search: find extension where file_path contains the basename.
    """
    row = conn.execute("""
        SELECT extension
        FROM files
        WHERE user_id = ? AND file_path LIKE ?
    """, (user_id, f"%{basename}%")).fetchone()
    return row[0] if row else None


def get_code_extensions_for_project(conn, user_id: int, project_name: str):
    """
    Return a list of file extensions for code files belonging to a project (latest version).
    """
    vk = get_latest_version_key(conn, user_id, project_name)
    if vk is None:
        return []
    rows = conn.execute("""
        SELECT extension
        FROM files
        WHERE user_id = ? AND version_key = ? AND file_type = 'code'
    """, (user_id, vk)).fetchall()
    return [r[0] for r in rows if r and r[0]]


def delete_files_for_project(conn, user_id: int, project_name: str):
    """
    Delete all files for the given user + project_name (all versions of that project).
    """
    version_keys = get_version_keys_for_project(conn, user_id, project_name)
    if not version_keys:
        return
    placeholders = ",".join("?" * len(version_keys))
    conn.execute(
        f"DELETE FROM files WHERE user_id = ? AND version_key IN ({placeholders})",
        (user_id, *version_keys),
    )


def get_files_with_timestamps(conn, user_id: int, project_name: str, version_key: Optional[int] = None):
    """
    Fetch files for a project with their timestamps.
    If version_key is None, uses latest version for project_name.
    Returns a list of dicts with file_name, file_path, created, modified, and file_type.
    """
    if conn is None:
        return []
    if version_key is None:
        version_key = get_latest_version_key(conn, user_id, project_name)
    if version_key is None:
        return []
    query = """
        SELECT file_name, file_path, created, modified, file_type
        FROM files
        WHERE user_id = ? AND version_key = ?
        ORDER BY modified ASC
    """
    rows = conn.execute(query, (user_id, version_key)).fetchall()
    return [
        {
            "file_name": r[0],
            "file_path": r[1],
            "created": r[2],
            "modified": r[3],
            "file_type": r[4],
        }
        for r in rows
    ]


def get_files_for_version(conn, user_id: int, version_key: int, only_text: bool = False):
    """
    Return file metadata for a specific version_key.
    [{'file_name', 'file_type', 'file_path'}, ...]
    """
    query = """
        SELECT file_name, file_type, file_path
        FROM files
        WHERE user_id = ? AND version_key = ?
    """
    params: list = [user_id, version_key]
    if only_text:
        query += " AND file_type = 'text'"
    rows = conn.execute(query, params).fetchall()
    return [
        {"file_name": r[0], "file_type": r[1], "file_path": r[2]}
        for r in rows
    ]
