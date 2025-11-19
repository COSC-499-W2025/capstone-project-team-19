import json

def store_github_repo_metrics(conn, user_id, project_name, owner, repo, metrics):
    """Store parsed GitHub metrics into the normalized database schema."""

    commits = metrics.get("commits", {})
    issues = metrics.get("issues", {})
    prs = metrics.get("pull_requests", {})
    contribs = metrics.get("contributions", {})

    # Commits
    total_commits = sum(commits.values()) if isinstance(commits, dict) else 0
    commit_days = len(commits) if isinstance(commits, dict) else 0
    first_commit_date = min(commits.keys()) if commits else None
    last_commit_date = max(commits.keys()) if commits else None

    # Issues
    issues_opened = issues.get("total_opened", 0)
    issues_closed = issues.get("total_closed", 0)

    # Pull Requests
    prs_opened = prs.get("total_opened", 0)
    prs_merged = prs.get("total_merged", 0)

    # Contributions
    total_additions = contribs.get("additions", 0)
    total_deletions = contribs.get("deletions", 0)
    contribution_percent = contribs.get("contribution_percent", 0.0)

    conn.execute("""
        INSERT INTO github_repo_metrics (
            user_id, project_name, repo_owner, repo_name,
            total_commits, commit_days, first_commit_date, last_commit_date,
            issues_opened, issues_closed,
            prs_opened, prs_merged,
            total_additions, total_deletions, contribution_percent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, repo_owner, repo_name)
        DO UPDATE SET
            total_commits = excluded.total_commits,
            commit_days = excluded.commit_days,
            first_commit_date = excluded.first_commit_date,
            last_commit_date = excluded.last_commit_date,
            issues_opened = excluded.issues_opened,
            issues_closed = excluded.issues_closed,
            prs_opened = excluded.prs_opened,
            prs_merged = excluded.prs_merged,
            total_additions = excluded.total_additions,
            total_deletions = excluded.total_deletions,
            contribution_percent = excluded.contribution_percent,
            last_synced = datetime('now')
    """, (
        user_id, project_name, owner, repo,
        total_commits, commit_days, first_commit_date, last_commit_date,
        issues_opened, issues_closed,
        prs_opened, prs_merged,
        total_additions, total_deletions, contribution_percent
    ))

    conn.commit()
    print(f"[GitHub] Stored metrics for {project_name}: commits={total_commits}, PRs={prs_opened}, issues={issues_opened}")

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