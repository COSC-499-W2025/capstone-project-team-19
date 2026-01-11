from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional


def delete_code_activity_metrics_for_project(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    scope: str,
) -> None:
    """
    Delete existing code activity metrics for a given user + project + scope.
    """
    conn.execute(
        """
        DELETE FROM code_activity_metrics
        WHERE user_id = ?
          AND project_name = ?
          AND scope = ?
        """,
        (user_id, project_name, scope),
    )


def insert_code_activity_metric(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    scope: str,
    source: str,        # 'files', 'prs', or 'combined'
    activity_type: str, # 'feature_coding', 'testing', ...
    event_count: int,
    total_events: int,
    percent: float,     # 0–100
) -> None:
    """
    Insert a single row into code_activity_metrics.
    """
    conn.execute(
        """
        INSERT INTO code_activity_metrics (
            user_id,
            project_name,
            scope,
            source,
            activity_type,
            event_count,
            total_events,
            percent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            project_name,
            scope,
            source,
            activity_type,
            event_count,
            total_events,
            percent,
        ),
    )


def store_code_activity_metrics(conn, user_id, summary):
    """
    Store activity metrics into code_activity_metrics table.
    - Clears old rows for this user + project + scope
    - Inserts rows for 'files', 'prs', and 'combined'
    """

    project_name = summary.project_name
    scope = summary.scope.value  # enum → string

    # 1) Delete old rows
    delete_code_activity_metrics_for_project(conn, user_id, project_name, scope)

    # 2) Insert files rows
    for at, data in summary.per_activity_files.items():
        insert_code_activity_metric(
            conn,
            user_id,
            project_name,
            scope,
            source="files",
            activity_type=at.value,
            event_count=data["count"],
            total_events=summary.total_file_events,
            percent=(data["count"] / summary.total_file_events * 100.0)
            if summary.total_file_events > 0 else 0.0,
        )

    # 3) Insert PR rows
    for at, data in summary.per_activity_prs.items():
        insert_code_activity_metric(
            conn,
            user_id,
            project_name,
            scope,
            source="prs",
            activity_type=at.value,
            event_count=data["count"],
            total_events=summary.total_pr_events,
            percent=(data["count"] / summary.total_pr_events * 100.0)
            if summary.total_pr_events > 0 else 0.0,
        )

    # 4) Insert combined rows
    for at, data in summary.per_activity.items():
        insert_code_activity_metric(
            conn,
            user_id,
            project_name,
            scope,
            source="combined",
            activity_type=at.value,
            event_count=data["count"],
            total_events=summary.total_events,
            percent=(data["count"] / summary.total_events * 100.0)
            if summary.total_events > 0 else 0.0,
        )

    conn.commit()


# =========================
# NEW: DB fetch helpers (no nesting needed elsewhere)
# =========================

def get_code_activity_percents(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    scope: str,
    source: str = "combined",
) -> Dict[str, float]:
    """
    Return {activity_type: percent} for a user+project+scope.
    Uses code_activity_metrics table.
    """
    rows = conn.execute(
        """
        SELECT activity_type, percent
        FROM code_activity_metrics
        WHERE user_id = ?
          AND project_name = ?
          AND scope = ?
          AND source = ?
        ORDER BY percent DESC
        """,
        (user_id, project_name, scope, source),
    ).fetchall()

    out: Dict[str, float] = {}
    for at, pct in rows or []:
        try:
            out[str(at)] = float(pct or 0.0)
        except Exception:
            out[str(at)] = 0.0
    return out


def get_normalized_code_metrics(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    is_collaborative: bool,
) -> Optional[Dict[str, int]]:
    """
    Normalize metrics from either:
      - code_collaborative_metrics (collab)
      - git_individual_metrics (individual)

    Returns:
      {
        "total_commits": int,
        "your_commits": int,
        "loc_added": int,
        "loc_deleted": int,
        "loc_net": int,
      }
    """
    if is_collaborative:
        row = conn.execute(
            """
            SELECT commits_all, commits_yours, loc_added, loc_deleted, loc_net
            FROM code_collaborative_metrics
            WHERE user_id = ? AND project_name = ?
            """,
            (user_id, project_name),
        ).fetchone()

        if not row:
            return None

        commits_all, commits_yours, loc_added, loc_deleted, loc_net = row

        return {
            "total_commits": int(commits_all or 0),
            "your_commits": int(commits_yours or 0),
            "loc_added": int(loc_added or 0),
            "loc_deleted": int(loc_deleted or 0),
            "loc_net": int(loc_net or 0),
        }

    # individual
    row = conn.execute(
        """
        SELECT total_commits, total_lines_added, total_lines_deleted, net_lines_changed
        FROM git_individual_metrics
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchone()

    if not row:
        return None

    total_commits, total_added, total_deleted, net_changed = row
    total_commits_i = int(total_commits or 0)

    return {
        "total_commits": total_commits_i,
        "your_commits": total_commits_i,  # individual project = your commits == total commits
        "loc_added": int(total_added or 0),
        "loc_deleted": int(total_deleted or 0),
        "loc_net": int(net_changed or 0),
    }

