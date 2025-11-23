"""
Handles all SQLite access needed for activity detection (files, PRs, classification).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import Scope


def _get_default_db_path() -> str:
    """
    Resolve <repo_root>/local_storage.db relative to this file.
    Assumes layout: <root>/local_storage.db and <root>/src/...
    """
    here = Path(__file__).resolve()
    # go up: code → activity_type → analysis → src → <root>
    root = here.parents[4]
    db_path = root / "local_storage.db"
    return str(db_path)


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open a SQLite connection with Row factory enabled.
    """
    if db_path is None:
        db_path = _get_default_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_project_classification(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return classification row (individual/collaborative, project_type) or None.
    """
    query = """
        SELECT classification, project_type, recorded_at
        FROM project_classifications
        WHERE user_id = ?
          AND project_name = ?
        ORDER BY recorded_at DESC
        LIMIT 1
    """
    with _get_connection(db_path) as conn:
        row = conn.execute(query, (user_id, project_name)).fetchone()
    return dict(row) if row else None


def get_project_files(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return all rows from `files` for this user + project_name.
    """
    query = """
        SELECT file_id, file_name, file_path, extension, file_type,
               created, modified, size_bytes
        FROM files
        WHERE user_id = ?
          AND project_name = ?
    """
    with _get_connection(db_path) as conn:
        rows = conn.execute(query, (user_id, project_name)).fetchall()
    return [dict(r) for r in rows]


def get_project_repos(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return linked repos for this project (to check if GitHub is connected).
    """
    query = """
        SELECT provider, repo_url, repo_full_name, repo_owner,
               repo_name, repo_id, default_branch, linked_at
        FROM project_repos
        WHERE user_id = ?
          AND project_name = ?
    """
    with _get_connection(db_path) as conn:
        rows = conn.execute(query, (user_id, project_name)).fetchall()
    return [dict(r) for r in rows]


def is_github_connected(
    user_id: int,
    db_path: Optional[str] = None,
) -> bool:
    """
    Return True if the user has at least one GitHub account linked.
    """
    query = """
        SELECT 1
        FROM github_accounts
        WHERE user_id = ?
        LIMIT 1
    """
    with _get_connection(db_path) as conn:
        row = conn.execute(query, (user_id,)).fetchone()
    return row is not None


def get_project_prs(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return PRs from `github_pull_requests` for this user + project.
    """
    query = """
        SELECT id,
               pr_number,
               pr_title,
               pr_body,
               labels_json,
               created_at,
               merged_at,
               state,
               merged
        FROM github_pull_requests
        WHERE user_id = ?
          AND project_name = ?
    """
    with _get_connection(db_path) as conn:
        rows = conn.execute(query, (user_id, project_name)).fetchall()
    return [dict(r) for r in rows]


def resolve_scope(
    classification_row: Optional[Dict[str, Any]],
) -> Scope:
    """
    Map classification string to Scope enum; default to COLLABORATIVE.
    """
    if not classification_row:
        return Scope.COLLABORATIVE

    cls = classification_row.get("classification")
    if cls == "individual":
        return Scope.INDIVIDUAL
    return Scope.COLLABORATIVE

def get_user_contributed_files(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return only files where this user actually contributed in a collaborative project.
    Joins `files` with `user_file_contributions` on (user_id, project_name, file_path).

    Only includes rows where lines_changed > 0 OR commits_count > 0.
    """
    query = """
        SELECT f.file_id,
               f.file_name,
               f.file_path,
               f.extension,
               f.file_type,
               f.created,
               f.modified,
               f.size_bytes
        FROM files AS f
        JOIN user_file_contributions AS ufc
          ON ufc.user_id = f.user_id
         AND ufc.project_name = f.project_name
         AND ufc.file_path = f.file_path
        WHERE f.user_id = ?
          AND f.project_name = ?
          AND (ufc.lines_changed > 0 OR ufc.commits_count > 0)
    """
    with _get_connection(db_path) as conn:
        rows = conn.execute(query, (user_id, project_name)).fetchall()
    return [dict(r) for r in rows]
