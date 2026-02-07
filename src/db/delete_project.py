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
      - dedup registry (projects, project_versions, version_files), which cascades into version_key-keyed metric tables
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
            # Tables keyed by (user_id, project_key). Explicit deletes so deletion works even when
            # PRAGMA foreign_keys is OFF (e.g. some test connections). When FK is ON, CASCADE would also remove these, redundant but safe.
            cur.execute(
                "DELETE FROM project_skills WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_summaries WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_feedback WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_rankings WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_thumbnails WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM config_files WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM text_contribution_summary WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_repos WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM project_drive_files WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM user_code_contributions WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM git_individual_metrics WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM code_collaborative_summary WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM code_collaborative_metrics WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )
            cur.execute(
                "DELETE FROM code_activity_metrics WHERE user_id = ? AND project_key = ?",
                (user_id, pk),
            )

            # Delete version_files first (depends on project_versions), then versions, then project row
            cur.execute(
                """
                DELETE FROM version_files
                WHERE version_key IN (
                    SELECT version_key FROM project_versions WHERE project_key = ?
                )
                """,
                (pk,),
            )
            cur.execute("DELETE FROM project_versions WHERE project_key = ?", (pk,))
            cur.execute("DELETE FROM projects WHERE project_key = ?", (pk,))

        # ---------------------------------------------------------------------
        # 1) Tables keyed directly by (user_id, project_name)
        # ---------------------------------------------------------------------
        tables_user_project = [
            "files",
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
        # 2) Optional DB hygiene (safe even if nothing is orphaned)
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


def delete_all_user_projects(conn: sqlite3.Connection, user_id: int) -> int:
    """
    Delete all projects for a user. Returns count of deleted projects.

    Deletes from both project_summaries and orphaned entries in the projects
    table (deduplication data from uploads that never completed analysis).
    """
    from src.db.project_summaries import get_project_summaries_list

    # Get project names from project_summaries
    summaries = get_project_summaries_list(conn, user_id)
    summary_names = {p["project_name"] for p in summaries}

    # Get orphaned project names from projects table (dedup data without summaries)
    orphan_rows = conn.execute(
        """
        SELECT p.display_name
        FROM projects p
        WHERE p.user_id = ?
        AND NOT EXISTS (
            SELECT 1
            FROM project_summaries ps
            WHERE ps.user_id = p.user_id
                AND ps.project_key = p.project_key
        );
        """,
            (user_id,),
    ).fetchall()
    orphan_names = {row[0] for row in orphan_rows}

    # Combine and delete all
    all_names = summary_names | orphan_names
    for project_name in all_names:
        delete_project_everywhere(conn, user_id, project_name)

    return len(all_names)
