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
