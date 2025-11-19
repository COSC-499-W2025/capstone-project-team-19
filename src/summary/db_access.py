# src/summary/db_access.py

def fetch_all_project_metadata(conn, user_id):
    return conn.execute("""
        SELECT project_name, classification, project_type
        FROM project_classifications
        WHERE user_id = ?
    """, (user_id,)).fetchall()


def fetch_github_metrics_row(conn, user_id, project_name):
    return conn.execute("""
        SELECT total_commits, commit_days, first_commit_date, last_commit_date,
               issues_opened, issues_closed,
               prs_opened, prs_merged,
               total_additions, total_deletions,
               contribution_percent
        FROM github_repo_metrics
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchone()
