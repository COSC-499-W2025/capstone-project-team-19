from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional


def upsert_project_thumbnail(
    conn: sqlite3.Connection,
    user_id: int,
    project_key: int,
    image_path: str,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO project_thumbnails (user_id, project_key, image_path, added_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_key) DO UPDATE SET
            image_path = excluded.image_path,
            updated_at = excluded.updated_at
        """,
        (user_id, project_key, image_path, now, now),
    )
    conn.commit()


def get_project_thumbnail_path(
    conn: sqlite3.Connection,
    user_id: int,
    project_key: int,
) -> Optional[str]:
    cur = conn.execute(
        """
        SELECT image_path
        FROM project_thumbnails
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, project_key),
    )
    row = cur.fetchone()
    return row[0] if row else None


def delete_project_thumbnail(
    conn: sqlite3.Connection,
    user_id: int,
    project_key: int,
) -> bool:
    cur = conn.execute(
        """
        DELETE FROM project_thumbnails
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, project_key),
    )
    conn.commit()
    return cur.rowcount > 0


def list_thumbnail_projects(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[str]:
    """Return display names of projects that have thumbnails (for UI compatibility)."""
    cur = conn.execute(
        """
        SELECT p.display_name
        FROM project_thumbnails pt
        JOIN projects p ON p.project_key = pt.project_key AND p.user_id = pt.user_id
        WHERE pt.user_id = ?
        ORDER BY p.display_name COLLATE NOCASE
        """,
        (user_id,),
    )
    return [r[0] for r in cur.fetchall()]
