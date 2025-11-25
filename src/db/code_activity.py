# src/db/code_activity.py

from __future__ import annotations

import sqlite3


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

def get_code_activity_metrics(conn, user_id: int, project_name: str) -> List[dict]:
    """
    Returns list of code activity events:
    - activity_type ('feature_coding', 'refactoring', etc.)
    - event_count
    - total_events
    - percent (0–100)
    """
    rows = conn.execute("""
        SELECT activity_type, event_count, total_events, percent
        FROM code_activity_metrics
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchall()

    return [
        {
            "activity_type": r[0],
            "event_count": r[1],
            "total_events": r[2],
            "percent": r[3],
        }
        for r in rows
    ] if rows else []