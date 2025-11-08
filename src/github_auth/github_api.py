import requests
from collections import defaultdict
import time

"""
Takes GitHub OAuth token as input
Makes authenticated API requests
Returns a sorted, deduplicated list of repositories attached to the user's GitHub account
"""

# Helper function for authenticated GET requests to GitHub API
# Raises runtime error on failure and returns parsed JSON
def gh_get(token: str, url: str):
    if not token:
        raise ValueError("GitHub token missing — user must authenticate first.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers = headers)

    if r.status_code != 200:
        raise RuntimeError(f"GitHub API request failed: {r.status_code}, {r.text}")

    return r.json()

def list_user_repos(token):
    personal_repos = gh_get(token, "https://api.github.com/user/repos?per_page=200")
    repos = [repo["full_name"] for repo in personal_repos]

    # Organizations the user is in
    orgs = gh_get(token, "https://api.github.com/user/orgs")
    for org in orgs:
        org_name = org["login"]
        org_repos = gh_get(token, f"https://api.github.com/orgs/{org_name}/repos?per_page=200")
        for repo in org_repos:
            if repo.get("permissions", {}).get("push"):
                repos.append(repo["full_name"])
       
    # Deduplicate and sort
    return sorted(set(repos), key = str.lower)

def get_authenticated_user(token):
    data = gh_get(token, "https://api.github.com/user")
    return {
        "login": data.get("login"),
        "id": data.get("id"),
        "name": data.get("name"),
        "email": data.get("email"),
        "profile_url": data.get("html_url")
    }

def get_gh_repo_metadata(owner, repo, token):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = gh_get(token, url)
    return data.get("id"), data.get("default_branch")

def get_gh_repo_commit_activity(token, owner, repo, username):
    page = 1
    daily = defaultdict(int)

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&per_page=100&page={page}"
        data = gh_get(token, url)

        # sometimes stats take longer to get, keep retrying until github api is returns data (as stated in the GitHub REST API documentation)
        if isinstance(data, dict) and data.get("message") == "202":
            return {"processing": True}

        if not data: break

        for commit in data:
            date_str = commit["commit"]["author"]["date"].split("T")[0]
            daily[date_str] += 1

        page += 1

    return dict(daily)

def get_gh_repo_language_breakdown(token, owner, repo):
    pass

def get_gh_repo_lines_added_and_deleted(token, owner, repo):
    pass

# gets PRs and issues, so aggregate this function to only get issues
def get_gh_repo_issues(token, owner, repo, github_username):    
    page = 1
    opened = defaultdict(int)
    closed = defaultdict(int)
    user_issues = []

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page={page}"
        data = gh_get(token, url) 
        
        if not data: break

        # skip PRs
        for issue in data:
            if "pull_request" in issue:
                continue

            title = issue.get("title")
            body = issue.get("body") or "" # in case body is empty
            created_at = issue.get("created_at", "").split("T")[0]
            closed_at = issue.get("closed_at")
            labels = [l["name"].lower() for l in issue.get("labels", [])]
            
            # track global issues
            opened[created_at] += 1
            if closed_at:
                closed[closed_at.split("T")[0]] += 1

            author = issue.get("user", {}).get("login", "")
            assignees = [a.get("login", "") for a in issue.get("assignees", [])]

            if github_username == author or github_username in assignees:
                user_issues.append({
                    "title": title,
                    "body": body,
                    "labels": labels,
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

def get_gh_repo_prs(token, owner, repo, github_username):
    page = 1
    opened = defaultdict(int)
    merged = defaultdict(int)
    user_prs = []

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=100&page={page}"
        data = gh_get(token, url)

        if not data: break

        for pr in data:
            author = pr.get("user", {}).get("login", "")
            if author != github_username: continue # getting only prs from user, not whole repo

            title = pr.get("title")
            body = pr.get("body") or ""
            created_at = pr.get("created_at", "").split("T")[0]
            merged_at = pr.get("merged_at")
            merged_date = merged_at.split("T")[0] if merged_at else None

            labels= [l["name"].lower() for l in pr.get("labels", [])]

            opened[created_at] += 1

            if merged_date:
                merged[merged_date] += 1

            user_prs.append({
                "title": title,
                "body": body,
                "labels": labels,
                "created_at": created_at,
                "merged_at": merged_date,
                "state": pr.get("state"),
                "merged": bool(merged_at)
            })

        page += 1

    return {
        "opened": dict(opened),
        "merged": dict(merged),
        "total_opened": sum(opened.values()),
        "total_merged": sum(merged.values()),
        "user_prs": user_prs
    }        

def get_gh_repo_contributions(token, owner, repo, github_username):
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
        
    # github sometimes returns 202 while calclating, keep polling up to 6 attempts in case it is calculating (as stated in documentation)
    for attempt in range(6): # 6 attempts
        data = gh_get(token, url)

        # GitHub returns a dict with message "202" while processing
        if isinstance(data, dict) and data.get("message") == "202":
            time.sleep(2)
            continue
        
        break # otherwise

    if isinstance(data, dict) and data.get("message") == "202":
        return {"processing": True}

    user_stats = {
        "commits": 0,
        "additions": 0,
        "deletions": 0,
        "contribution_percent": 0.0
    }

    total_repo_commits = 0
    user_total = 0

    for contributor in data:
        total_repo_commits += contributor.get("total", 0)

        if contributor.get("author", {}).get("login") == github_username:
            user_total = contributor.get("total", 0)
            user_stats["commits"] = user_total
            
            for week in contributor.get("weeks", []):
                user_stats["additions"] += week.get("a", 0)
                user_stats["deletions"] += week.get("d", 0)

    if total_repo_commits > 0:
        user_stats["contribution_percent"] = round(
            (user_total / total_repo_commits) * 100, 2
        )

    return user_stats

def get_gh_repo_readme(token, owner, repo): pass
def get_gh_repo_content_analysis(token, owner, repo): pass
def get_gh_repo_pulls(token, owner, repo): pass
def get_gh_repo_reviews(token, owner, repo): pass