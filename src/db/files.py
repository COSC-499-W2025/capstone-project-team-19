"""
src/db/files.py

User-uploaded file database operations:
 - Handles retrieval of file metadata such as project_name and file_type.
"""


import sqlite3
from typing import List, Tuple


def get_files_for_user(conn: sqlite3.Connection, user_id: int) -> List[Tuple[str, str]]:
    """
    Return all (project_name, file_type) pairs for files that belong to a given user
    and have a non-null project_name.
    """
    rows = conn.execute("""
        SELECT project_name, file_type
        FROM files
        WHERE user_id = ? AND project_name IS NOT NULL
    """, (user_id,)).fetchall()

    return rows


def get_recent_file_paths_for_project(conn, project_name, limit=200):
    """
    Return up to `limit` file paths for a given project_name,
    ordered by modified timestamp (newest first).
    """
    rows = conn.execute("""
        SELECT DISTINCT file_path
        FROM files
        WHERE project_name = ?
        ORDER BY modified DESC
        LIMIT ?
    """, (project_name, limit)).fetchall()

    return [r[0] for r in rows if r and r[0]]


def get_code_files_for_project(conn, user_id: int, project_name: str):
    """
    Return all (file_name, file_path) pairs for code files
    belonging to a user + project_name.
    """
    rows = conn.execute("""
        SELECT file_name, file_path
        FROM files
        WHERE user_id = ? AND project_name = ? AND file_type = 'code'
    """, (user_id, project_name)).fetchall()

    return rows

def get_files_for_project(conn, user_id: int, project_name: str, only_text: bool = False):
    """
    Return a list of dicts with file metadata for a given project:
        [{'file_name', 'file_type', 'file_path'}, ...]
    """
    query = """
        SELECT file_name, file_type, file_path
        FROM files
        WHERE user_id = ? AND project_name = ?
    """
    params = [user_id, project_name]

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

def get_code_extensions_for_project(conn, project_name: str):
    """
    Return a list of file extensions for code files belonging to a project.
    """
    rows = conn.execute("""
        SELECT extension
        FROM files
        WHERE project_name = ? AND file_type = 'code'
    """, (project_name,)).fetchall()

    return [r[0] for r in rows if r and r[0]]

def delete_files_for_project(conn, user_id: int, project_name: str):
    """
    Delete all files for a specific user + project_name.
    """
    conn.execute("""
        DELETE FROM files
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))

def get_files_with_timestamps(conn, user_id: int, project_name: str, version_key: int | None = None):
    """
    Fetch files for a project with their timestamps.
    Returns a list of dicts with file_name, file_path, created, modified, and file_type.
    """
    if conn is None:
        return []

    query = """
        SELECT file_name, file_path, created, modified, file_type
        FROM files
        WHERE user_id = ? AND project_name = ?
    """
    params: list[object] = [user_id, project_name]
    if version_key is not None:
        query += " AND version_key = ?"
        params.append(version_key)
    query += " ORDER BY modified ASC"

    rows = conn.execute(query, params).fetchall()
    return [
        {
            'file_name': r[0],
            'file_path': r[1],
            'created': r[2],
            'modified': r[3],
            'file_type': r[4]
        }
        for r in rows
    ]
