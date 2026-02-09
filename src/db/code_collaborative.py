from __future__ import annotations
import sqlite3
from typing import Any, Mapping, Optional

from .projects import get_project_key
from .deduplication import insert_project


def insert_code_collaborative_metrics(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    payload: Mapping[str, Any],
) -> None:
    """
    Basic upsert for collaborative code metrics.

    All values in `payload` must already be normalized:
    - datetimes → ISO strings
    - list fields → JSON strings
    - missing fields handled by caller
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        pk = insert_project(conn, user_id, project_name)
    conn.execute(
        """
        INSERT INTO code_collaborative_metrics (
            user_id,
            project_key,
            repo_path,

            commits_all,
            commits_yours,
            commits_coauth,
            merges,

            loc_added,
            loc_deleted,
            loc_net,
            files_touched,
            new_files,
            renames,

            first_commit_at,
            last_commit_at,
            commits_L30,
            commits_L90,
            commits_L365,
            longest_streak,
            current_streak,
            top_days,
            top_hours,

            languages_json,
            folders_json,
            top_files_json,
            frameworks_json
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_id, project_key) DO UPDATE SET
            repo_path       = excluded.repo_path,
            commits_all     = excluded.commits_all,
            commits_yours   = excluded.commits_yours,
            commits_coauth  = excluded.commits_coauth,
            merges          = excluded.merges,
            loc_added       = excluded.loc_added,
            loc_deleted     = excluded.loc_deleted,
            loc_net         = excluded.loc_net,
            files_touched   = excluded.files_touched,
            new_files       = excluded.new_files,
            renames         = excluded.renames,
            first_commit_at = excluded.first_commit_at,
            last_commit_at  = excluded.last_commit_at,
            commits_L30     = excluded.commits_L30,
            commits_L90     = excluded.commits_L90,
            commits_L365    = excluded.commits_L365,
            longest_streak  = excluded.longest_streak,
            current_streak  = excluded.current_streak,
            top_days        = excluded.top_days,
            top_hours       = excluded.top_hours,
            languages_json  = excluded.languages_json,
            folders_json    = excluded.folders_json,
            top_files_json  = excluded.top_files_json,
            frameworks_json = excluded.frameworks_json
        """,
        (
            user_id,
            pk,
            payload["repo_path"],
            payload["commits_all"],
            payload["commits_yours"],
            payload["commits_coauth"],
            payload["merges"],
            payload["loc_added"],
            payload["loc_deleted"],
            payload["loc_net"],
            payload["files_touched"],
            payload["new_files"],
            payload["renames"],
            payload["first_commit_at"],
            payload["last_commit_at"],
            payload["commits_L30"],
            payload["commits_L90"],
            payload["commits_L365"],
            payload["longest_streak"],
            payload["current_streak"],
            payload["top_days"],
            payload["top_hours"],
            payload["languages_json"],
            payload["folders_json"],
            payload["top_files_json"],
            payload["frameworks_json"],
        ),
    )
    conn.commit()


def get_metrics_id(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[int]:
    """
    Return the id from code_collaborative_metrics for this (user_id, project_name),
    or None if no row exists.
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        return None
    row = conn.execute(
        """
        SELECT id
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, pk),
    ).fetchone()
    return row[0] if row else None


def insert_code_collaborative_summary(
    conn: sqlite3.Connection,
    metrics_id: int,
    user_id: int,
    project_name: str,
    summary_type: str,
    content: str,
) -> None:
    """
    Insert a collaborative code summary row.

    summary_type:
      - 'non-llm' for manual user input
      - 'llm' for LLM-generated summary (project + contribution text in one blob)
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        pk = insert_project(conn, user_id, project_name)
    conn.execute(
        """
        INSERT INTO code_collaborative_summary (
            metrics_id,
            user_id,
            project_key,
            summary_type,
            content
        )
        VALUES (?,?,?,?,?)
        """,
        (
            metrics_id,
            user_id,
            pk,
            summary_type,
            content,
        ),
    )
    conn.commit()
