from __future__ import annotations

import sqlite3


def delete_project_everywhere(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> None:
    """
    Hard-delete all stored data for a (user_id, project_name) pair, INCLUDING dedup tables.

    This removes:
      - project_classifications (and any CASCADE-linked metric tables)
      - project_summaries, project_skills, project_feedback, project_rankings, thumbnails
      - files/config_files
      - per-project activity metrics
      - GitHub + Drive + code contribution tables
      - dedup registry: projects, project_versions, version_files

    NOTE: Does not touch user-level auth tables (github_accounts, user_tokens, etc.).
    """

    # Strongly recommended globally in your DB init, but harmless to run here too:
    # conn.execute("PRAGMA foreign_keys = ON;")

    with conn:
        cur = conn.cursor()

        # ---------------------------------------------------------------------
        # 0) Delete dedup registry for this display name (projects/version_files)
        # ---------------------------------------------------------------------
        # projects has no UNIQUE(user_id, display_name), so handle multiple matches safely.
        project_keys = [
            row[0]
            for row in cur.execute(
                """
                SELECT project_key
                FROM projects
                WHERE user_id = ? AND display_name = ?
                """,
                (user_id, project_name),
            ).fetchall()
        ]

        for pk in project_keys:
            # Delete version_files first (depends on project_versions)
            cur.execute(
                """
                DELETE FROM version_files
                WHERE version_key IN (
                    SELECT version_key FROM project_versions WHERE project_key = ?
                )
                """,
                (pk,),
            )
            # Then versions, then the project row
            cur.execute("DELETE FROM project_versions WHERE project_key = ?", (pk,))
            cur.execute("DELETE FROM projects WHERE project_key = ?", (pk,))

        # ---------------------------------------------------------------------
        # 1) Delete classification rows (cascades into metric tables via FK)
        # ---------------------------------------------------------------------
        cur.execute(
            """
            DELETE FROM project_classifications
            WHERE user_id = ? AND project_name = ?
            """,
            (user_id, project_name),
        )

        # ---------------------------------------------------------------------
        # 2) Tables keyed directly by (user_id, project_name)
        # ---------------------------------------------------------------------
        tables_user_project = [
            "files",
            "config_files",
            "project_summaries",
            "project_skills",
            "project_feedback",     
            "project_rankings",    
            "project_thumbnails",   
            "text_contribution_summary",
            "project_repos",
            "project_drive_files",
            "user_code_contributions",
            "code_activity_metrics",
            "code_collaborative_metrics",
            "code_collaborative_summary",
            "git_individual_metrics",
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
                f"DELETE FROM {table} WHERE user_id = ? AND project_name = ?",
                (user_id, project_name),
            )

        # ---------------------------------------------------------------------
        # 3) Optional DB hygiene (safe even if nothing is orphaned)
        # ---------------------------------------------------------------------
        # If earlier deletes left orphan rows due to FK settings, this cleans them.
        cur.execute(
            """
            DELETE FROM project_versions
            WHERE project_key NOT IN (SELECT project_key FROM projects)
            """
        )
        cur.execute(
            """
            DELETE FROM version_files
            WHERE version_key NOT IN (SELECT version_key FROM project_versions)
            """
        )