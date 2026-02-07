from __future__ import annotations
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .projects import get_project_key

def get_project_summary_row(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch a single project_summaries row for a user + project_name.

    Returns a dict with:
      - project_summary_id
      - user_id
      - project_name
      - project_type
      - project_mode
      - created_at
      - summary_json (raw string)
      - summary (parsed JSON dict, or {} on parse error)
    """
    cur = conn.execute(
        """
        SELECT
            project_summary_id,
            user_id,
            project_key,
            (SELECT display_name FROM projects WHERE project_key = project_summaries.project_key) AS project_name,
            project_type,
            project_mode,
            summary_json,
            created_at
        FROM project_summaries
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, int(get_project_key(conn, user_id, project_name) or -1)),
    )
    row = cur.fetchone()
    if row is None:
        return None

    (
        project_summary_id,
        row_user_id,
        project_key,
        display_name,
        project_type,
        project_mode,
        summary_json,
        created_at,
    ) = row

    try:
        summary_parsed = json.loads(summary_json)
    except json.JSONDecodeError:
        summary_parsed = {}

    return {
        "project_summary_id": project_summary_id,
        "user_id": row_user_id,
        "project_key": project_key,
        "project_name": display_name or project_name,
        "project_type": project_type,
        "project_mode": project_mode,
        "created_at": created_at,
        "summary_json": summary_json,
        "summary": summary_parsed,
    }


def get_code_activity_percentages(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    scope: str,
    source: str = "combined",
) -> List[Tuple[str, float]]:
    """
    Return activity_type -> percent for a code project from code_activity_metrics.

    Filters by:
      - user_id
      - project_name
      - scope ('individual' or 'collaborative')
      - source ('files', 'prs', or 'combined')

    Returns a list of (activity_type, percent) sorted by percent DESC,
    excluding entries where percent == 0.
    """
    cur = conn.execute(
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
    )
    rows = cur.fetchall()
    return [
        (activity_type, percent)
        for (activity_type, percent) in rows
        if percent and percent > 0
    ]


def get_code_collaborative_duration(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """
    Fetch first_commit_at and last_commit_at for a collaborative code project.

    Priority:
      1. Manual dates from project_summaries table (if set)
      2. Automatic dates from code_collaborative_metrics

    Returns:
      (first_commit_at, last_commit_at) as strings, or None if no row found.
    """
    cur = conn.execute(
        """
        SELECT
            COALESCE(ps.manual_start_date, ccm.first_commit_at) AS first_commit,
            COALESCE(ps.manual_end_date, ccm.last_commit_at) AS last_commit
        FROM code_collaborative_metrics ccm
        LEFT JOIN projects p
            ON p.user_id = ccm.user_id
        AND p.display_name = ccm.project_name
        LEFT JOIN project_summaries ps
            ON ps.user_id = ccm.user_id
        AND ps.project_key = p.project_key
        WHERE ccm.user_id = ?
        AND ccm.project_name = ?
        LIMIT 1;
        """,
        (user_id, project_name),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return row[0], row[1]


def get_code_collaborative_non_llm_summary(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[str]:
    """
    Fetch the latest non-LLM summary content for a collaborative code project.

    Uses code_collaborative_summary where summary_type = 'non-llm'.
    Returns the content string, or None if not available.
    """
    cur = conn.execute(
        """
        SELECT content
        FROM code_collaborative_summary
        WHERE user_id = ?
          AND project_name = ?
          AND summary_type = 'non-llm'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, project_name),
    )
    row = cur.fetchone()
    return row[0] if row is not None else None

def get_text_duration(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """
    Fetch start_date and end_date for a text project.

    Priority:
      1. Manual dates from project_summaries table (if set)
      2. Automatic dates from text_activity_contribution

    Returns:
      (start_date, end_date) as strings, or None if no dates found.
    """
    cur = conn.execute(
        """
        WITH latest_version AS (
            SELECT pv.version_key
            FROM project_versions pv
            JOIN projects p ON p.project_key = pv.project_key
            WHERE p.user_id = ? AND p.display_name = ?
            ORDER BY pv.version_key DESC
            LIMIT 1
        )
        SELECT
            COALESCE(ps.manual_start_date, tac.start_date) AS start_date,
            COALESCE(ps.manual_end_date, tac.end_date) AS end_date
        FROM latest_version lv
        LEFT JOIN text_activity_contribution tac
            ON lv.version_key = tac.version_key
        LEFT JOIN projects p
            ON p.user_id = ?
        AND p.display_name = ?
        LEFT JOIN project_summaries ps
            ON ps.user_id = p.user_id
        AND ps.project_key = p.project_key
        ORDER BY tac.generated_at DESC
        LIMIT 1;
        """,
        (user_id, project_name, user_id, project_name),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return row[0], row[1]

def get_code_individual_duration(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> Optional[tuple[str | None, str | None]]:
    """
    Return (first_commit_date, last_commit_date) for an individual code project.

    Priority:
      1. Manual dates from project_summaries table (if set)
      2. Automatic dates from git_individual_metrics

    Returns None if there is no row or both dates are missing.
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        return None
    cur = conn.execute(
        """
        SELECT
            COALESCE(ps.manual_start_date, gim.first_commit_date) AS first_commit,
            COALESCE(ps.manual_end_date, gim.last_commit_date) AS last_commit
        FROM git_individual_metrics gim
        LEFT JOIN project_summaries ps
            ON ps.user_id = gim.user_id
            AND ps.project_key = gim.project_key
        WHERE gim.user_id = ?
        AND gim.project_key = ?;
        """,
        (user_id, pk),
    )
    row = cur.fetchone()
    if row is None:
        return None

    first, last = row[0], row[1]
    if not first and not last:
        return None

    return first, last
