import json
try:
    from src import constants
except ModuleNotFoundError:
    import constants

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

    # Contributions - user stats
    user_contribs = contribs.get("user", {})
    total_additions = user_contribs.get("additions", 0)
    total_deletions = user_contribs.get("deletions", 0)
    contribution_percent = user_contribs.get("contribution_percent", 0.0)
    
    # Team-wide stats
    team_contribs = contribs.get("team", {})
    team_total_commits = team_contribs.get("total_commits", 0)
    team_total_additions = team_contribs.get("total_additions", 0)
    team_total_deletions = team_contribs.get("total_deletions", 0)

    conn.execute("""
        INSERT INTO github_repo_metrics (
            user_id, project_name, repo_owner, repo_name,
            total_commits, commit_days, first_commit_date, last_commit_date,
            issues_opened, issues_closed,
            prs_opened, prs_merged,
            total_additions, total_deletions, contribution_percent,
            team_total_commits, team_total_additions, team_total_deletions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            team_total_commits = excluded.team_total_commits,
            team_total_additions = excluded.team_total_additions,
            team_total_deletions = excluded.team_total_deletions,
            last_synced = datetime('now')
    """, (
        user_id, project_name, owner, repo,
        total_commits, commit_days, first_commit_date, last_commit_date,
        issues_opened, issues_closed,
        prs_opened, prs_merged,
        total_additions, total_deletions, contribution_percent,
        team_total_commits, team_total_additions, team_total_deletions
    ))

    conn.commit()

    if constants.VERBOSE:
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

def print_github_metrics_summary(repo_metrics: dict):
    """Pretty-print GitHub contributions for a project."""

    print("\n==============================")
    print("   GitHub Activity Summary")
    print("==============================")

    print(f"Total commits:        {repo_metrics.get('total_commits', 0)}")
    print(f"Active commit days:   {repo_metrics.get('commit_days', 0)}")

    print(f"First commit:         {repo_metrics.get('first_commit_date')}")
    print(f"Last commit:          {repo_metrics.get('last_commit_date')}")

    print("\nIssues:")
    print(f" - Opened:            {repo_metrics.get('issues_opened', 0)}")
    print(f" - Closed:            {repo_metrics.get('issues_closed', 0)}")

    print("\nPull Requests:")
    print(f" - Opened:            {repo_metrics.get('prs_opened', 0)}")
    print(f" - Merged:            {repo_metrics.get('prs_merged', 0)}")

    print("\nLines Changed:")
    print(f" - Additions:         {repo_metrics.get('total_additions', 0)}")
    print(f" - Deletions:         {repo_metrics.get('total_deletions', 0)}")

    print(f"\nContribution Percent: {repo_metrics.get('contribution_percent', 0)}%")
    print("==============================\n")


def store_github_detailed_metrics(conn, user_id, project_name, owner, repo, metrics):
    """Store detailed GitHub metrics (issues, PRs, reviews, timestamps) into separate tables."""
    
    issues = metrics.get("issues", {})
    prs = metrics.get("pull_requests", {})
    commit_timestamps = metrics.get("commit_timestamps", [])
    reviews = metrics.get("reviews", {})
    
    # Clear existing data for this repo to avoid duplicates
    conn.execute("""
        DELETE FROM github_issues 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    conn.execute("""
        DELETE FROM github_issue_comments 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    conn.execute("""
        DELETE FROM github_pull_requests 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    conn.execute("""
        DELETE FROM github_commit_timestamps 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    conn.execute("""
        DELETE FROM github_pr_reviews 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    conn.execute("""
        DELETE FROM github_pr_review_comments 
        WHERE user_id = ? AND project_name = ? AND repo_owner = ? AND repo_name = ?
    """, (user_id, project_name, owner, repo))
    
    # Store user issues
    user_issues = issues.get("user_issues", [])
    for issue in user_issues:
        conn.execute("""
            INSERT INTO github_issues (
                user_id, project_name, repo_owner, repo_name,
                issue_title, issue_body, labels_json, created_at, closed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, project_name, owner, repo,
            issue.get("title"),
            issue.get("body"),
            json.dumps(issue.get("labels", [])),
            issue.get("created_at"),
            issue.get("closed_at")
        ))
    
    # Store user issue comments
    user_issue_comments = issues.get("user_issue_comments", [])
    for comment in user_issue_comments:
        conn.execute("""
            INSERT INTO github_issue_comments (
                user_id, project_name, repo_owner, repo_name,
                issue_number, comment_body, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, project_name, owner, repo,
            comment.get("issue_number"),
            comment.get("body"),
            comment.get("created_at")
        ))
    
    # Store user PRs
    user_prs = prs.get("user_prs", [])
    for pr in user_prs:
        conn.execute("""
            INSERT INTO github_pull_requests (
                user_id, project_name, repo_owner, repo_name,
                pr_number, pr_title, pr_body, labels_json, created_at, merged_at, state, merged
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, project_name, owner, repo,
            pr.get("number"),
            pr.get("title"),
            pr.get("body"),
            json.dumps(pr.get("labels", [])),
            pr.get("created_at"),
            pr.get("merged_at"),
            pr.get("state"),
            1 if pr.get("merged") else 0
        ))
    
    # Store commit timestamps
    for timestamp in commit_timestamps:
        # Convert datetime to string if needed
        ts_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
        conn.execute("""
            INSERT INTO github_commit_timestamps (
                user_id, project_name, repo_owner, repo_name, commit_timestamp
            )
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, project_name, owner, repo, ts_str))
    
    # Store PR reviews
    for pr_number, review_data in reviews.items():
        reviews_list = review_data.get("reviews", [])
        for review in reviews_list:
            conn.execute("""
                INSERT INTO github_pr_reviews (
                    user_id, project_name, repo_owner, repo_name, pr_number, review_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, project_name, owner, repo,
                pr_number,
                json.dumps(review)
            ))
        
        # Store review comments
        review_comments = review_data.get("review_comments", [])
        for comment in review_comments:
            conn.execute("""
                INSERT INTO github_pr_review_comments (
                    user_id, project_name, repo_owner, repo_name, pr_number, comment_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, project_name, owner, repo,
                pr_number,
                json.dumps(comment)
            ))
    
    conn.commit()
    
    if constants.VERBOSE:
        print(f"[GitHub] Stored detailed metrics: {len(user_issues)} issues, {len(user_prs)} PRs, {len(commit_timestamps)} commits, {len(reviews)} PR reviews")