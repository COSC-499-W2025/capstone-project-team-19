"""
src/db/github_pull_requests.py

GitHub pull request-related read operations.
"""

import sqlite3
from typing import List, Dict


def get_pull_requests_for_project(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> List[Dict]:
    """
    Return PR rows for this user + project as plain dicts.
    """
    rows = conn.execute(
        """
        SELECT
            id,
            pr_number,
            pr_title,
            pr_body,
            labels_json,
            created_at,
            merged_at,
            state,
            merged
        FROM github_pull_requests
        WHERE user_id = ?
          AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchall()

    result: List[Dict] = []
    for r in rows:
        # sqlite3.Row supports .keys() and index access by column name
        if hasattr(r, "keys"):
            d = {k: r[k] for k in r.keys()}
        else:
            # tuple fallback (unlikely if you use Row factory)
            d = {
                "id": r[0],
                "pr_number": r[1],
                "pr_title": r[2],
                "pr_body": r[3],
                "labels_json": r[4],
                "created_at": r[5],
                "merged_at": r[6],
                "state": r[7],
                "merged": r[8],
            }
        result.append(d)

    return result
