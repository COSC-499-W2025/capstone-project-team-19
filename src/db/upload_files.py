from __future__ import annotations
import sqlite3

def _zip_scope_like_patterns(zip_stem: str) -> tuple[str, str]:
    """
    Return (p1, p2) LIKE patterns that match this upload's extracted paths.
    Mirrors src/services/uploads_service._rows_for_project_scoped_to_upload().
    """
    return (f"%/{zip_stem}/%", f"{zip_stem}/%")

def delete_upload_files_for_project(conn: sqlite3.Connection, *, user_id: int, project_name: str, zip_stem: str) -> None:
    """
    Delete parsed rows for a project *scoped to a specific upload*.
    Applies to both `files` and `config_files`.
    """
    p1, p2 = _zip_scope_like_patterns(zip_stem)
    conn.execute(
        """
        DELETE FROM files
        WHERE user_id = ? AND project_name = ?
          AND (file_path LIKE ? OR file_path LIKE ?)
        """,
        (user_id, project_name, p1, p2),
    )
    conn.execute(
        """
        DELETE FROM config_files
        WHERE user_id = ? AND project_name = ?
          AND (file_path LIKE ? OR file_path LIKE ?)
        """,
        (user_id, project_name, p1, p2),
    )

def rename_upload_files_project(conn: sqlite3.Connection, *, user_id: int, old_project_name: str, new_project_name: str, zip_stem: str) -> None:
    """
    Rename project_name for parsed rows scoped to this upload.
    Applies to both `files` and `config_files`.
    """
    p1, p2 = _zip_scope_like_patterns(zip_stem)
    conn.execute(
        """
        UPDATE files
        SET project_name = ?
        WHERE user_id = ? AND project_name = ?
          AND (file_path LIKE ? OR file_path LIKE ?)
        """,
        (new_project_name, user_id, old_project_name, p1, p2),
    )
    conn.execute(
        """
        UPDATE config_files
        SET project_name = ?
        WHERE user_id = ? AND project_name = ?
          AND (file_path LIKE ? OR file_path LIKE ?)
        """,
        (new_project_name, user_id, old_project_name, p1, p2),
    )

def attach_version_key_to_upload_files(conn: sqlite3.Connection, *, user_id: int, project_name: str, version_key: int, zip_stem: str) -> None:
    """
    Backfill files.version_key for this upload's rows for a project.
    Only sets version_key where currently NULL.
    """
    p1, p2 = _zip_scope_like_patterns(zip_stem)
    conn.execute(
        """
        UPDATE files
        SET version_key = ?
        WHERE user_id = ? AND project_name = ? AND version_key IS NULL
          AND (file_path LIKE ? OR file_path LIKE ?)
        """,
        (int(version_key), user_id, project_name, p1, p2),
    )