"""
src/db/project_summaries.py

Handles storage and retrieval of project summaries.
"""

import sqlite3
import json


def save_project_summary(conn, user_id, project_name, summary_json):
    """
    Inserts or replaces a summary for a project.
    
    Args:
        conn: SQLite connection
        user_id: User ID
        project_name: Project name
        summary_json: JSON string representing ProjectSummary.__dict__
    
    Uses INSERT OR REPLACE to avoid duplicates based on (user_id, project_name).
    """
    # Extract project_type and project_mode from the JSON if available
    try:
        summary_dict = json.loads(summary_json)
        project_type = summary_dict.get("project_type")
        project_mode = summary_dict.get("project_mode")
    except (json.JSONDecodeError, AttributeError):
        project_type = None
        project_mode = None
    
    conn.execute("""
        INSERT OR REPLACE INTO project_summaries (
            user_id,
            project_name,
            project_type,
            project_mode,
            summary_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, project_name, project_type, project_mode, summary_json))
    conn.commit()

def get_all_user_project_summaries(conn, user_id):
    """
    Retrieve ALL summaries for a specific user
    """

    cursor = conn.execute("""
        SELECT *
        FROM project_summaries
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()

    col_names = [desc[0] for desc in cursor.description]

    return [dict(zip(col_names, row)) for row in rows]


def get_project_summaries_list(conn, user_id):
    """
    Retrieve a list of all project summaries for a user.
    """
    rows = conn.execute("""
        SELECT project_summary_id, project_name, project_type, project_mode, created_at
        FROM project_summaries
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    return [
        {
            "project_summary_id": row[0],
            "project_name": row[1],
            "project_type": row[2],
            "project_mode": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]


def get_project_summary_by_name(conn, user_id, project_name):
    """
    Retrieve a specific project summary by project name.
    """
    row = conn.execute("""
        SELECT project_summary_id, project_name, project_type, project_mode, summary_json, created_at
        FROM project_summaries
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchone()

    if not row:
        return None

    return {
        "project_summary_id": row[0],
        "project_name": row[1],
        "project_type": row[2],
        "project_mode": row[3],
        "summary_json": row[4],
        "created_at": row[5]
    }


def get_all_projects_with_dates(conn, user_id):
    """
    Returns all projects for a user ordered by actual project completion date (newest first).
    Prioritizes manual_end_date if set, otherwise uses automatic dates.
    Returns list of dicts with keys: project_name, actual_project_date
    """
    query = """
        WITH latest_classification AS (
            SELECT pc.project_name,
                   pc.project_type,
                   pc.classification_id
            FROM project_classifications pc
            WHERE pc.user_id = ?
              AND pc.classification_id = (
                  SELECT pc2.classification_id
                  FROM project_classifications pc2
                  WHERE pc2.user_id = pc.user_id
                    AND pc2.project_name = pc.project_name
                  ORDER BY pc2.recorded_at DESC, pc2.classification_id DESC
                  LIMIT 1
              )
        ),
        project_dates AS (
            SELECT 
                ps.project_name,
                COALESCE(
                    ps.manual_end_date,
                    CASE
                        WHEN lc.project_type = 'text' THEN tac.end_date
                        WHEN lc.project_type = 'code' THEN
                            COALESCE(
                                grm.last_commit_date,
                                json_extract(ps.summary_json, '$.metrics.git.commit_stats.last_commit_date'),
                                json_extract(ps.summary_json, '$.metrics.collaborative_git.last_commit_date')
                            )
                        ELSE NULL
                    END
                ) AS actual_project_date
            FROM project_summaries ps
            LEFT JOIN latest_classification lc
                ON ps.user_id = ?  -- Note: need user_id in join for safety
                AND ps.project_name = lc.project_name
            LEFT JOIN text_activity_contribution tac
                ON lc.classification_id = tac.classification_id
            LEFT JOIN github_repo_metrics grm
                ON ps.user_id = grm.user_id
                AND ps.project_name = grm.project_name
            WHERE ps.user_id = ?
        )
        SELECT 
            project_name,
            MAX(actual_project_date) AS actual_project_date
        FROM project_dates
        GROUP BY project_name
        ORDER BY 
            actual_project_date DESC NULLS LAST,
            project_name;
    """

    rows = conn.execute(query, (user_id, user_id, user_id)).fetchall()

    return [
        {
            "project_name": row[0],
            "actual_project_date": row[1]
        }
        for row in rows
    ]

# Manual date override functions

def set_project_dates(conn, user_id, project_name, start_date, end_date):
    conn.execute(
        """
        UPDATE project_summaries
        SET manual_start_date = ?, manual_end_date = ?
        WHERE user_id = ? AND project_name = ?
        """,
        (start_date, end_date, user_id, project_name)
    )
    conn.commit()


def get_project_dates(conn, user_id, project_name):
    row = conn.execute(
        """
        SELECT manual_start_date, manual_end_date
        FROM project_summaries
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name)
    ).fetchone()

    return row if row else None


def clear_project_dates(conn, user_id, project_name):
    conn.execute(
        """
        UPDATE project_summaries
        SET manual_start_date = NULL, manual_end_date = NULL
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name)
    )
    conn.commit()


def clear_all_project_dates(conn, user_id):
    conn.execute(
        """
        UPDATE project_summaries
        SET manual_start_date = NULL, manual_end_date = NULL
        WHERE user_id = ?
        """,
        (user_id,)
    )
    conn.commit()


def get_all_manual_dates(conn, user_id):
    rows = conn.execute(
        """
        SELECT project_name, manual_start_date, manual_end_date
        FROM project_summaries
        WHERE user_id = ?
          AND (manual_start_date IS NOT NULL OR manual_end_date IS NOT NULL)
        ORDER BY project_name ASC
        """,
        (user_id,)
    ).fetchall()

    return rows