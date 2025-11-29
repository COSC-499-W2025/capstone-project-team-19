from __future__ import annotations
import json
import sqlite3
from typing import Any, Mapping, Optional
from datetime import datetime

def insert_code_collaborative_metrics(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    metrics: Mapping[str, Any],
) -> None:
    """
    Upsert collaborative code metrics for (user_id, project_name) into
    code_collaborative_metrics using data from the compute_metrics() dict.

    Safely handles:
      - missing metric sections
      - missing focus fields
      - datetime objects (converted to ISO strings)
    """

    totals = metrics.get("totals", {}) or {}
    loc = metrics.get("loc", {}) or {}
    history = metrics.get("history", {}) or {}
    focus = metrics.get("focus", {}) or {}

    repo_path = metrics.get("path") or metrics.get("project_path") or ""

    # Normalize optional focus lists
    languages = focus.get("languages") or []
    folders = focus.get("folders") or []
    top_files = focus.get("top_files") or []
    frameworks = focus.get("frameworks") or []

    # Convert datetime → ISO string
    def _to_iso(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    first_commit = _to_iso(history.get("first"))
    last_commit = _to_iso(history.get("last"))

    conn.execute(
        """
        INSERT INTO code_collaborative_metrics (
            user_id,
            project_name,
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
        ON CONFLICT(user_id, project_name) DO UPDATE SET
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
            project_name,
            repo_path,
            # totals
            totals.get("commits_all"),
            totals.get("commits_yours"),
            totals.get("commits_coauth"),
            totals.get("merges"),
            # loc
            loc.get("added"),
            loc.get("deleted"),
            loc.get("net"),
            loc.get("files_touched"),
            loc.get("new_files"),
            loc.get("renames"),
            # history (ISO strings)
            first_commit,
            last_commit,
            history.get("L30"),
            history.get("L90"),
            history.get("L365"),
            history.get("longest_streak"),
            history.get("current_streak"),
            history.get("top_days"),
            history.get("top_hours"),
            # focus (JSON)
            json.dumps(languages),
            json.dumps(folders),
            json.dumps(top_files),
            json.dumps(frameworks),
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
    row = conn.execute(
        """
        SELECT id
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
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
    conn.execute(
        """
        INSERT INTO code_collaborative_summary (
            metrics_id,
            user_id,
            project_name,
            summary_type,
            content
        )
        VALUES (?,?,?,?,?)
        """,
        (
            metrics_id,
            user_id,
            project_name,
            summary_type,
            content,
        ),
    )
    conn.commit()
