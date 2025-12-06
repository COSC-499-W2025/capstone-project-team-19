from .github_api import get_gh_repo_commit_activity, get_gh_repo_issues, get_gh_repo_prs, get_gh_repo_contributions, get_repo_commit_timestamps, get_gh_reviews_for_repo, get_all_issue_comments

def fetch_github_metrics(token, owner, repo, gh_username):
    commit_activity = get_gh_repo_commit_activity(token, owner, repo, gh_username)
    all_issue_comments = get_all_issue_comments(token, owner, repo) # one call for all comments
    user_prs = get_gh_repo_prs(token, owner, repo, gh_username)
    user_issues = get_gh_repo_issues(token, owner, repo, gh_username, all_issue_comments)
    user_contributions = get_gh_repo_contributions(token, owner, repo, gh_username)
    commit_timestamps = get_repo_commit_timestamps(token, owner, repo)

    user_pr_numbers = [
        pr["number"] for pr in user_prs.get("user_prs", [])
    ]

    review_data = get_gh_reviews_for_repo(token, owner, repo, user_pr_numbers)

    # get PR discussion comments locally
    pr_numbers_set = set(user_pr_numbers)

    pr_discussion_comments = [
        c for c in all_issue_comments
        if int(c["issue_url"].split("/")[-1]) in pr_numbers_set
    ]

    return {
        "repository": f"{owner}/{repo}",
        "username": gh_username,
        "commits": commit_activity,
        "issues": user_issues,
        "pull_requests": user_prs,
        "contributions": user_contributions,
        "commit_timestamps": commit_timestamps,
        "reviews": review_data,
        "pr_discussion_comments": pr_discussion_comments,
    }