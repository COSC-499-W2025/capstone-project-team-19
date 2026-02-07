"""
src/db/skills.py

Manages skill-metric database operations:
 - Storing and retrieving skills
"""

import sqlite3
import json
from typing import List, Dict, Any

from .projects import get_project_key
from .deduplication import insert_project


def _get_or_create_project_key(conn: sqlite3.Connection, user_id: int, project_name: str) -> int:
    """
    Resolve a project's canonical key from its display name.
    Creates the project row if missing (best-effort for tests/legacy callers).
    """
    pk = get_project_key(conn, user_id, project_name)
    if pk is None:
        pk = insert_project(conn, user_id, project_name)
        conn.commit()
    return int(pk)


def insert_project_skill(conn, user_id, project_name, skill_name, level, score, evidence):
    """
    Insert or update a skill entry for a project.
    Ensures only one row per (user_id, project_name, skill_name).
    """
    project_key = _get_or_create_project_key(conn, user_id, project_name)

    conn.execute(
        """
        INSERT INTO project_skills (user_id, project_key, skill_name, level, score, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_key, skill_name)
        DO UPDATE SET
            level = excluded.level,
            score = excluded.score,
            evidence_json = excluded.evidence_json
        ;
        """,
        (user_id, project_key, skill_name, level, score, evidence)
    )


def get_project_skills(conn, user_id, project_name):
    """
    Retrieve all skills for a project with their details.
    Returns list of tuples: (skill_name, level, score, evidence_json)
    """
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        return []
    cursor = conn.execute(
        """
        SELECT skill_name, level, score, evidence_json
        FROM project_skills
        WHERE user_id = ? AND project_key = ? AND score > 0
        ORDER BY score DESC
        """,
        (user_id, int(project_key))
    )
    
    return cursor.fetchall()

def get_skill_events(conn, user_id):
    """
    Returns every skill a user has practices, including:
        - skill_name
        - level
        - score
        - project_name
        - actual_activity_date (end_date for text, last_commit_date for code, NULL if neither exists)
        - recorded_at (upload/classification date, always present)

    For code projects, last_commit_date is retrieved from:
        1. Manual override from project_summaries.manual_end_date (if set)
        2. git_individual_metrics.last_commit_date (individual projects)
        3. code_collaborative_metrics.last_commit_at (collaborative projects)
        4. github_repo_metrics.last_commit_date (if GitHub connection exists)
        5. project_summaries.summary_json->metrics->git->commit_stats->last_commit_date (fallback)
        6. project_summaries.summary_json->metrics->collaborative_git->last_commit_date (fallback)

    For text projects, end_date is retrieved from:
        1. Manual override from project_summaries.manual_end_date (if set)
        2. text_activity_contribution.end_date (automatic detection)

    Returns tuples: (skill_name, level, score, project_name, actual_activity_date, recorded_at)
    """

    query = """
        WITH latest_version AS (
            SELECT
                p.user_id,
                p.project_key,
                p.display_name AS project_name,
                p.project_type,
                (
                    SELECT pv2.version_key
                    FROM project_versions pv2
                    WHERE pv2.project_key = p.project_key
                    ORDER BY pv2.version_key DESC
                    LIMIT 1
                ) AS version_key,
                (
                    SELECT pv3.created_at
                    FROM project_versions pv3
                    WHERE pv3.project_key = p.project_key
                    ORDER BY pv3.version_key DESC
                    LIMIT 1
                ) AS recorded_at
            FROM projects p
            WHERE p.user_id = ?
        )
        SELECT
            ps.skill_name,
            ps.level,
            ps.score,
            lv.project_name,
            COALESCE(
                ps_summary.manual_end_date,
                CASE
                    WHEN lv.project_type = 'text' THEN tac.end_date
                    WHEN lv.project_type = 'code' THEN
                        COALESCE(
                            gim.last_commit_date,
                            ccm.last_commit_at,
                            grm.last_commit_date,
                            json_extract(ps_summary.summary_json, '$.metrics.git.commit_stats.last_commit_date'),
                            json_extract(ps_summary.summary_json, '$.metrics.collaborative_git.last_commit_date')
                        )
                    ELSE NULL
                END
            ) AS actual_activity_date,
            lv.recorded_at
        FROM project_skills ps
        INNER JOIN latest_version lv
            ON ps.user_id = lv.user_id
            AND ps.project_key = lv.project_key
        LEFT JOIN text_activity_contribution tac
            ON lv.version_key = tac.version_key
        LEFT JOIN git_individual_metrics gim
            ON ps.user_id = gim.user_id
            AND lv.project_key = gim.project_key
        LEFT JOIN code_collaborative_metrics ccm
            ON ps.user_id = ccm.user_id
            AND lv.project_name = ccm.project_name
        LEFT JOIN github_repo_metrics grm
            ON ps.user_id = grm.user_id
            AND lv.project_name = grm.project_name
        LEFT JOIN project_summaries ps_summary
            ON ps.user_id = ps_summary.user_id
            AND ps.project_key = ps_summary.project_key
        WHERE
            ps.user_id = ?
            AND ps.score > 0
        ORDER BY
            actual_activity_date ASC NULLS LAST,
            lv.recorded_at ASC,
            lv.project_name,
            ps.score DESC;
    """

    # user_id is used twice: once in the CTE, once in the main WHERE.
    return conn.execute(query, (user_id, user_id)).fetchall()