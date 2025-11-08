from src.github.github_api import get_gh_repo_commit_activity, get_gh_repo_issues, get_gh_repo_prs, get_gh_repo_contributions
def fetch_github_metrics(token, owner, repo, gh_username):
    commit_activity = get_gh_repo_commit_activity(token, owner, repo, gh_username)
    user_issues = get_gh_repo_issues(token, owner, repo, gh_username)
    user_prs = get_gh_repo_prs(token, owner, repo, gh_username)
    user_contributions = get_gh_repo_contributions(token, owner, repo, gh_username)

    return {
        "repository": f"{owner}/{repo}",
        "username": gh_username,
        "commits": commit_activity,
        "issues": user_issues,
        "pull_requests": user_prs,
        "contributions": user_contributions
    }