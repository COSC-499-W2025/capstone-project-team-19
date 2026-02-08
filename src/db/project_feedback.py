# src/db/project_feedback.py

from __future__ import annotations
import json
import sqlite3
from typing import Any, Dict, List, Optional


def clear_project_feedback(conn: sqlite3.Connection, user_id: int, project_name: str) -> None:
    conn.execute(
        """
        DELETE FROM project_feedback
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    )
    conn.commit()


def upsert_project_feedback(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    project_type: str,              # "text" or "code"
    skill_name: str,                # bucket name
    criterion_key: str,             # stable id
    criterion_label: str,           # human title
    expected: Optional[str] = None,
    observed: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    file_name: str = "",
) -> None:
    observed_json = json.dumps(observed or {}, ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO project_feedback (
            user_id, project_name, project_type, skill_name,
            file_name, criterion_key, criterion_label,
            expected, observed_json, suggestion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, skill_name, file_name, criterion_key)
        DO UPDATE SET
            project_type    = excluded.project_type,
            criterion_label = excluded.criterion_label,
            expected        = excluded.expected,
            observed_json   = excluded.observed_json,
            suggestion      = excluded.suggestion,
            generated_at    = datetime('now')
        """,
        (
            user_id, project_name, project_type, skill_name,
            file_name, criterion_key, criterion_label,
            expected, observed_json, suggestion
        ),
    )
    conn.commit()


def list_projects_with_feedback(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT project_name, project_type, COUNT(*) AS issues
        FROM project_feedback
        WHERE user_id = ?
        GROUP BY project_name, project_type
        ORDER BY issues DESC, project_name ASC
        """,
        (user_id,),
    )
    return [
        {"project_name": r[0], "project_type": r[1], "issues": r[2]}
        for r in cur.fetchall()
    ]


def get_project_feedback(conn: sqlite3.Connection, user_id: int, project_name: str) -> List[Dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT
            feedback_id, project_type, skill_name, file_name,
            criterion_key, criterion_label, expected,
            observed_json, suggestion, generated_at
        FROM project_feedback
        WHERE user_id = ? AND project_name = ?
        ORDER BY skill_name ASC, file_name ASC, criterion_key ASC
        """,
        (user_id, project_name),
    )

    rows = []
    for r in cur.fetchall():
        rows.append({
            "feedback_id": r[0],
            "project_type": r[1],
            "skill_name": r[2],
            "file_name": r[3],
            "criterion_key": r[4],
            "criterion_label": r[5],
            "expected": r[6],
            "observed": json.loads(r[7]) if r[7] else {},
            "suggestion": r[8],
            "generated_at": r[9],
        })
    return rows
