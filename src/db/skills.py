"""
src/db/skills.py

Manages skill-metric database operations:
 - Storing and retrieving skills
"""

import sqlite3
import json
from typing import List, Dict, Any


def insert_project_skill(conn, user_id, project_name, skill_name, level, score, evidence):
    """
    Insert or update a skill entry for a project.
    Ensures only one row per (user_id, project_name, skill_name).
    """

    conn.execute(
        """
        INSERT INTO project_skills (user_id, project_name, skill_name, level, score, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, skill_name)
        DO UPDATE SET
            level = excluded.level,
            score = excluded.score,
            evidence_json = excluded.evidence_json
        ;
        """,
        (user_id, project_name, skill_name, level, score, evidence)
    )


def get_project_skills(conn, user_id, project_name):
    """
    Retrieve all skills for a project with their details.
    Returns list of tuples: (skill_name, level, score, evidence_json)
    """
    cursor = conn.execute(
        """
        SELECT skill_name, level, score, evidence_json
        FROM project_skills
        WHERE user_id = ? AND project_name = ? AND score > 0
        ORDER BY score DESC
        """,
        (user_id, project_name)
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
        1. github_repo_metrics.last_commit_date (if GitHub connection exists)
        2. project_summaries.summary_json->metrics->git->commit_stats->last_commit_date (individual projects with local git)
        3. project_summaries.summary_json->metrics->collaborative_git->last_commit_date (collaborative projects with local git)
    
    Returns tuples: (skill_name, level, score, project_name, actual_activity_date, recorded_at)
    """

    query = """
        SELECT 
            ps.skill_name, 
            ps.level, 
            ps.score, 
            ps.project_name,
            CASE
                WHEN pc.project_type = 'text' THEN tac.end_date
                WHEN pc.project_type = 'code' THEN 
                    COALESCE(
                        grm.last_commit_date,
                        json_extract(ps_summary.summary_json, '$.metrics.git.commit_stats.last_commit_date'),
                        json_extract(ps_summary.summary_json, '$.metrics.collaborative_git.last_commit_date')
                    )
                ELSE NULL
            END AS actual_activity_date,
            pc.recorded_at
        FROM project_skills ps
        INNER JOIN project_classifications pc
            ON ps.user_id = pc.user_id
            AND ps.project_name = pc.project_name
        LEFT JOIN text_activity_contribution tac
            ON pc.classification_id = tac.classification_id
        LEFT JOIN github_repo_metrics grm
            ON ps.user_id = grm.user_id
            AND ps.project_name = grm.project_name
        LEFT JOIN project_summaries ps_summary
            ON ps.user_id = ps_summary.user_id
            AND ps.project_name = ps_summary.project_name
        WHERE 
            ps.user_id = ?
            AND ps.score > 0
        ORDER BY 
            actual_activity_date ASC NULLS LAST,
            pc.recorded_at ASC,
            ps.project_name,
            ps.score DESC;
    """

    return conn.execute(query, (user_id,)).fetchall()