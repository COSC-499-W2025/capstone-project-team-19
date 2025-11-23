from .github_api import get_gh_repo_commit_activity, get_gh_repo_issues, get_gh_repo_prs, get_gh_repo_contributions, get_repo_commit_timestamps, get_gh_reviews_for_repo

def fetch_github_metrics(token, owner, repo, gh_username):
    commit_activity = get_gh_repo_commit_activity(token, owner, repo, gh_username)
    user_issues = get_gh_repo_issues(token, owner, repo, gh_username)
    user_prs = get_gh_repo_prs(token, owner, repo, gh_username)
    user_contributions = get_gh_repo_contributions(token, owner, repo, gh_username)
    commit_timestamps = get_repo_commit_timestamps(token, owner, repo)
    user_pr_numbers = [
        pr_obj["number"]
        for pr_obj in user_prs.get("user_prs", [])
        if "number" in pr_obj
    ]
    review_data = get_gh_reviews_for_repo(token, owner, repo, user_pr_numbers)

    return {
        "repository": f"{owner}/{repo}",
        "username": gh_username,
        "commits": commit_activity,
        "issues": user_issues,
        "pull_requests": user_prs,
        "contributions": user_contributions,
        "commit_timestamps": commit_timestamps,
        "reviews": review_data,
    }