from __future__ import annotations
import sqlite3, json
from typing import Any, Dict, Optional

def store_local_git_metrics_collaborative(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    metrics: Dict[str, Any]
) -> None:
    """
    Upsert aggregated git metrics for collaborative code projects.
    Table defined in schema/tables.sql.
    """
    totals = metrics.get("totals", {}) or {}
    loc = metrics.get("loc", {}) or {}
    history = metrics.get("history", {}) or {}
    focus = metrics.get("focus", {}) or {}

    def _iso(dt_obj):
        try:
            return dt_obj.isoformat()
        except Exception:
            return None

    conn.execute(
        """
        INSERT INTO local_git_metrics_collaborative (
            user_id, project_name, repo_path,

            commits_all, commits_yours, commits_coauth, merges,
            loc_added, loc_deleted, loc_net, files_touched, new_files, renames,

            first_commit_at, last_commit_at,
            commits_L30, commits_L90, commits_L365,
            longest_streak, current_streak,
            top_days, top_hours,

            languages_json, folders_json, top_files_json, frameworks_json,
            desc
        )
        VALUES (
            :user_id, :project_name, :repo_path,

            :commits_all, :commits_yours, :commits_coauth, :merges,
            :loc_added, :loc_deleted, :loc_net, :files_touched, :new_files, :renames,

            :first_commit_at, :last_commit_at,
            :commits_L30, :commits_L90, :commits_L365,
            :longest_streak, :current_streak,
            :top_days, :top_hours,

            :languages_json, :folders_json, :top_files_json, :frameworks_json,
            :desc
        )
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
            frameworks_json = excluded.frameworks_json,

            desc            = excluded.desc
        """,
        {
            "user_id": user_id,
            "project_name": project_name,
            "repo_path": metrics.get("path") or "",
            "commits_all": totals.get("commits_all"),
            "commits_yours": totals.get("commits_yours"),
            "commits_coauth": totals.get("commits_coauth"),
            "merges": totals.get("merges"),
            "loc_added": loc.get("added"),
            "loc_deleted": loc.get("deleted"),
            "loc_net": loc.get("net"),
            "files_touched": loc.get("files_touched"),
            "new_files": loc.get("new_files"),
            "renames": loc.get("renames"),
            "first_commit_at": _iso(history.get("first")),
            "last_commit_at": _iso(history.get("last")),
            "commits_L30": history.get("L30"),
            "commits_L90": history.get("L90"),
            "commits_L365": history.get("L365"),
            "longest_streak": history.get("longest_streak"),
            "current_streak": history.get("current_streak"),
            "top_days": history.get("top_days"),
            "top_hours": history.get("top_hours"),
            "languages_json": json.dumps(focus.get("languages") or []),
            "folders_json": json.dumps(focus.get("folders") or []),
            "top_files_json": json.dumps(focus.get("top_files") or []),
            "frameworks_json": json.dumps(focus.get("frameworks") or []),
            "desc": metrics.get("desc"),
        },
    )
    conn.commit()
