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