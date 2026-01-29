from __future__ import annotations

import sqlite3


def delete_project_everywhere(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> None:
    """
    Hard-delete all stored data for a (user_id, project_name) pair.

    This removes:
      - project_classifications (and any CASCADE-linked metric tables)
      - project_summaries, project_skills
      - files/config_files
      - per-project activity metrics
      - GitHub + Drive + code contribution tables

    NOTE: This does *not* touch github_accounts or other user-level auth tables.
    """

    cur = conn.cursor()

    # 1) Delete classification rows (cascades into non_llm_text, non_llm_code_individual,
    #    text_activity_contribution, etc. via FK).
    cur.execute(
        """
        DELETE FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    )

    # 2) Tables keyed directly by (user_id, project_name)
    tables_user_project = [
        "files",
        "config_files",
        "project_summaries",
        "project_skills",
        "text_contribution_summary",
        "project_repos",
        "project_drive_files",
        "user_code_contributions",
        "code_activity_metrics",
        "code_collaborative_metrics",
        "code_collaborative_summary",
        "github_repo_metrics",
        "github_collaboration_profiles",
        "github_issues",
        "github_issue_comments",
        "github_pull_requests",
        "github_commit_timestamps",
        "github_pr_reviews",
        "github_pr_review_comments",
    ]

    for table in tables_user_project:
        cur.execute(
            f"""
            DELETE FROM {table}
            WHERE user_id = ? AND project_name = ?
            """,
            (user_id, project_name),
        )

    conn.commit()
    
def delete_dedup_records_for_project(conn, user_id: int, project_name: str) -> None:
    row = conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (user_id, project_name),
    ).fetchone()
    if not row:
        return

    project_key = row[0]

    # delete children first
    conn.execute(
        """
        DELETE FROM version_files
        WHERE version_key IN (
            SELECT version_key FROM project_versions WHERE project_key = ?
        )
        """,
        (project_key,),
    )
    conn.execute("DELETE FROM project_versions WHERE project_key = ?", (project_key,))
    conn.execute("DELETE FROM projects WHERE project_key = ?", (project_key,))

