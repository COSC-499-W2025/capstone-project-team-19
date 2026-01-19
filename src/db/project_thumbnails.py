from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional


def upsert_project_thumbnail(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    image_path: str,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO project_thumbnails (user_id, project_name, image_path, added_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name) DO UPDATE SET
            image_path = excluded.image_path,
            updated_at = excluded.updated_at
        """,
        (user_id, project_name, image_path, now, now),
    )
    conn.commit()


def get_project_thumbnail_path(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[str]:
    cur = conn.execute(
        """
        SELECT image_path
        FROM project_thumbnails
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    )
    row = cur.fetchone()
    return row[0] if row else None


def delete_project_thumbnail(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> bool:
    cur = conn.execute(
        """
        DELETE FROM project_thumbnails
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    )
    conn.commit()
    return cur.rowcount > 0


def list_thumbnail_projects(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[str]:
    cur = conn.execute(
        """
        SELECT project_name
        FROM project_thumbnails
        WHERE user_id = ?
        ORDER BY project_name COLLATE NOCASE
        """,
        (user_id,),
    )
    return [r[0] for r in cur.fetchall()]
