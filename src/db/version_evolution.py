"""
src/db/version_evolution.py

Per-version evolution data for project evolution showcase.
Feeds: GET /projects/{id}/evolution, future skills timeline, heatmap.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from .projects import get_project_key


def insert_version_summary(conn: sqlite3.Connection, version_key: int, summary_text: Optional[str] = None, activity_date: Optional[str] = None, lines_added: Optional[int] = None, lines_deleted: Optional[int] = None, total_words: Optional[int] = None) -> None:
    """Snapshot version-level summary and diff-related stats."""
    conn.execute(
        """
        INSERT OR REPLACE INTO version_summaries
            (version_key, summary_text, activity_date, lines_added, lines_deleted, total_words)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (version_key, summary_text or None, activity_date, lines_added, lines_deleted, total_words),
    )
    conn.commit()


def insert_version_skills_from_project(conn: sqlite3.Connection, user_id: int, project_name: str, version_key: int) -> None:
    """Copy current project_skills into version_skills for this version."""
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        return
    rows = conn.execute(
        """
        SELECT skill_name, level, score
        FROM project_skills
        WHERE user_id = ? AND project_key = ? AND score > 0
        """,
        (user_id, int(project_key)),
    ).fetchall()
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO version_skills (version_key, skill_name, level, score)
        VALUES (?, ?, ?, ?)
        """,
        [(version_key, r[0], r[1], r[2]) for r in rows],
    )
    conn.commit()


def get_version_summary(conn: sqlite3.Connection, version_key: int) -> Optional[Dict[str, Any]]:
    """Get version_summaries row for a version."""
    row = conn.execute(
        """
        SELECT summary_text, activity_date, lines_added, lines_deleted, total_words, created_at
        FROM version_summaries WHERE version_key = ?
        """,
        (version_key,),
    ).fetchone()
    if not row:
        return None
    return {
        "summary_text": row[0],
        "activity_date": row[1],
        "lines_added": row[2],
        "lines_deleted": row[3],
        "total_words": row[4],
        "created_at": row[5],
    }


def get_version_skills(conn: sqlite3.Connection, version_key: int) -> List[Dict[str, Any]]:
    """Get skills for a version."""
    rows = conn.execute(
        """
        SELECT skill_name, level, score
        FROM version_skills
        WHERE version_key = ?
        ORDER BY score DESC
        """,
        (version_key,),
    ).fetchall()
    return [{"skill_name": r[0], "level": r[1], "score": r[2]} for r in rows]


def get_version_keys_ordered_for_project(conn: sqlite3.Connection, project_key: int) -> List[tuple[int, str]]:
    """
    Return (version_key, created_at) for all versions of a project, oldest first.
    """
    rows = conn.execute(
        """
        SELECT version_key, created_at
        FROM project_versions
        WHERE project_key = ?
        ORDER BY version_key ASC
        """,
        (project_key,),
    ).fetchall()
    return [(int(r[0]), r[1] or "") for r in rows]
