"""
src/db/github_repositories.py

GitHub repository-related database operations:
 - Storing project-to-repository mappings
 - Retrieving repository information
"""

import sqlite3
from typing import Optional
import json

def save_project_repo(conn: sqlite3.Connection, user_id: int, project_name: str, repo_url: str, repo_full_name: str, repo_owner: str, repo_name: str, repo_id: int, default_branch: str, provider="github"):
    # Store which GitHub repository corresponds to a given collaborative project
    
    conn.execute("""
        INSERT OR REPLACE INTO project_repos (
            user_id, 
            project_name, 
            provider, 
            repo_url,
            repo_full_name,
            repo_owner,
            repo_name,
            repo_id,
            default_branch
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, project_name, provider, repo_url, repo_full_name, repo_owner, repo_name, repo_id, default_branch))

    conn.commit()


def get_project_repo(conn: sqlite3.Connection, user_id: int, project_name: str, provider="github") -> Optional[str]:
    # Fetch mapped GitHub repo URL for this project, if exists
    
    row = conn.execute("""
        SELECT repo_url FROM project_repos
        WHERE user_id=? AND project_name=? AND provider=?
        LIMIT 1
    """, (user_id, project_name, provider)).fetchone()

    return row[0] if row else None

def store_collaboration_profile(conn, user_id, project_name, owner, repo, profile):
    conn.execute("""
        INSERT INTO github_collaboration_profiles (
            user_id, project_name, repo_owner, repo_name, profile_json
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, repo_owner, repo_name)
        DO UPDATE SET
            profile_json = excluded.profile_json,
            updated_at = datetime('now')
    """, (
        user_id, project_name, owner, repo, json.dumps(profile)
    ))

    conn.commit()

# get a github repositories metrics from the local db
def get_github_repo_metrics(conn, user_id, project_name, owner, repo):
    """Retrieve stored GitHub metrics for a given project from the normalized table."""
    cur = conn.execute("""
        SELECT
            total_commits,
            commit_days,
            first_commit_date,
            last_commit_date,
            issues_opened,
            issues_closed,
            prs_opened,
            prs_merged,
            total_additions,
            total_deletions,
            contribution_percent,
            team_total_commits,
            team_total_additions,
            team_total_deletions,
            last_synced
        FROM github_repo_metrics
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
        LIMIT 1
    """, (user_id, project_name, owner, repo))

    row = cur.fetchone()
    if not row:
        return None

    keys = [d[0] for d in cur.description]
    return dict(zip(keys, row))