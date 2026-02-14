from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.image_utils import save_standardized_thumbnail, validate_image_path


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


def store_thumbnail(
    conn: sqlite3.Connection,
    user_id: int,
    project_key: int,
    project_name: str,
    image_path: Path,
    images_dir: Path,
) -> Path:
    """Validate, standardize, and persist a thumbnail image.

    Returns the destination path of the stored PNG.
    Raises ValueError on invalid image.
    """
    src = validate_image_path(str(image_path))
    dst = save_standardized_thumbnail(src, images_dir, user_id, project_name)
    upsert_project_thumbnail(conn, user_id, project_key, str(dst))
    return dst


def delete_thumbnail_and_file(
    conn: sqlite3.Connection,
    user_id: int,
    project_key: int,
    images_dir: Path,
) -> bool:
    """Delete thumbnail DB record and remove the file from disk.

    Returns True if a record was deleted, False if nothing to delete.
    """
    image_path = get_project_thumbnail_path(conn, user_id, project_key)
    if image_path is None:
        return False
    delete_project_thumbnail(conn, user_id, project_key)
    p = Path(image_path)
    if p.exists() and p.parent.resolve() == images_dir.resolve():
        p.unlink(missing_ok=True)
    return True
