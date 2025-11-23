import os
from collections import defaultdict
import requests

# -------------------
# Shared API Helper
# -------------------
def gh_get(token: str, url: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    # GitHub sometimes returns 202 when stats aren't ready yet
    if r.status_code == 202:
        return {"processing": True}

    if r.status_code != 200:
        raise RuntimeError(f"GitHub API request failed: {r.status_code}, {r.text}")

    return r.json()

# -------------------
# Core Functions
# -------------------
def get_authenticated_user(token):
    data = gh_get(token, "https://api.github.com/user")
    return {
        "login": data.get("login"),
        "id": data.get("id"),
        "name": data.get("name"),
        "email": data.get("email"),
        "profile_url": data.get("html_url")
    }

def get_gh_repo_commit_activity(token, owner, repo, username):
    page = 1
    daily = defaultdict(int)

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&per_page=100&page={page}"
        data = gh_get(token, url)

        if isinstance(data, dict) and data.get("processing"):
            return {"processing": True}

        if not data:
            break

        for commit in data:
            date_str = commit["commit"]["author"]["date"].split("T")[0]
            daily[date_str] += 1

        page += 1

    return dict(daily)

def get_gh_repo_issues(token, owner, repo, github_username):
    page = 1
    opened = defaultdict(int)
    closed = defaultdict(int)
    user_issues = []

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page={page}"
        data = gh_get(token, url)

        if not data:
            break

        for issue in data:
            # Skip PRs
            if "pull_request" in issue:
                continue

            created_at = issue.get("created_at", "").split("T")[0]
            closed_at = issue.get("closed_at")

            opened[created_at] += 1
            if closed_at:
                closed[closed_at.split("T")[0]] += 1

            author = issue.get("user", {}).get("login", "")
            assignees = [a.get("login", "") for a in issue.get("assignees", [])]

            # Only store user-involved issues
            if github_username == author or github_username in assignees:
                user_issues.append({
                    "title": issue.get("title"),
                    "body": issue.get("body") or "",
                    "labels": [l["name"].lower() for l in issue.get("labels", [])],
                    "created_at": created_at,
                    "closed_at": closed_at.split("T")[0] if closed_at else None
                })

        page += 1

    return {
        "opened": dict(opened),
        "closed": dict(closed),
        "total_opened": sum(opened.values()),
        "total_closed": sum(closed.values()),
        "user_issues": user_issues
    }

def get_gh_repo_contributions(token, owner, repo, github_username):
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
    data = gh_get(token, url)

    if isinstance(data, dict) and data.get("processing"):
        return {"processing": True}

    stats = {
        "commits": 0,
        "additions": 0,
        "deletions": 0,
        "contribution_percent": 0.0
    }

    total_repo_commits = 0

    for contributor in data:
        total_repo_commits += contributor.get("total", 0)

        if contributor.get("author", {}).get("login") == github_username:
            stats["commits"] = contributor.get("total", 0)
            for week in contributor.get("weeks", []):
                stats["additions"] += week.get("a", 0)
                stats["deletions"] += week.get("d", 0)

    if total_repo_commits > 0:
        stats["contribution_percent"] = round((stats["commits"] / total_repo_commits) * 100, 2)

    return stats

# -------------------
# Manual tests below
# -------------------
if __name__ == "__main__":
    token = input("Paste GitHub token: ").strip()
    owner = input("Repo owner username: ").strip()
    repo = input("Repo name: ").strip()
    username = input("Your GitHub username: ").strip()

    print("\n=== User Info ===")
    print(get_authenticated_user(token))

    print("\n=== Commit Activity ===")
    print(get_gh_repo_commit_activity(token, owner, repo, username))

    print("\n=== Issue Activity ===")
    print(get_gh_repo_issues(token, owner, repo, username))

    print("\n=== Contribution Stats ===")
    print(get_gh_repo_contributions(token, owner, repo, username))
