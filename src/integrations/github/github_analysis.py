from .github_api import (
    get_gh_repo_commit_activity,
    get_gh_repo_issues,
    get_gh_repo_contributions,
    get_repo_commit_timestamps,
    get_all_issue_comments
)
from .github_analysis_graphql import fetch_pr_collaboration_graphql


def fetch_github_metrics(token, owner, repo, gh_username):
    # Fast REST endpoints
    commit_activity = get_gh_repo_commit_activity(token, owner, repo, gh_username)
    all_issue_comments = get_all_issue_comments(token, owner, repo)
    user_issues = get_gh_repo_issues(token, owner, repo, gh_username, all_issue_comments)
    contributions = get_gh_repo_contributions(token, owner, repo, gh_username)
    commit_timestamps = get_repo_commit_timestamps(token, owner, repo)

    # GraphQL: ALL PR-related collaboration
    pr_collab = fetch_pr_collaboration_graphql(
        token,
        owner,
        repo,
        gh_username
    )

    # Transform graphql_prs to pull_requests format for storage functions
    user_prs = pr_collab.get("user_prs", [])
    pull_requests = {
        "total_opened": pr_collab.get("prs_opened", 0),
        "total_merged": sum(1 for pr in user_prs if pr.get("merged")),
        "user_prs": user_prs
    }
    
    # Extract reviews from graphql_prs
    reviews = pr_collab.get("reviews", {})

    return {
        "repository": f"{owner}/{repo}",
        "username": gh_username,

        # REST
        "commits": commit_activity,
        "issues": user_issues,
        "contributions": contributions,
        "commit_timestamps": commit_timestamps,

        # GraphQL
        "graphql_prs": pr_collab,
        "pull_requests": pull_requests,
        "reviews": reviews,
    }