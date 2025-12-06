import requests
from collections import defaultdict
import time
from datetime import datetime

"""
Takes GitHub OAuth token as input
Makes authenticated API requests
Returns a sorted, deduplicated list of repositories attached to the user's GitHub account
"""

# Helper function for authenticated GET requests to GitHub API
# Raises runtime error on failure and returns parsed JSON
def gh_get(token: str, url: str, retries: int = 6, delay: int = 2):
    if not token:
        raise ValueError("GitHub token missing — user must authenticate first.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers)

            # GitHub stats endpoints sometimes return 202 while processing
            if r.status_code == 202:
                time.sleep(delay)
                continue

            # Any other error
            if r.status_code != 200:
                try:
                    err_json = r.json()
                    msg = err_json.get("message", "").strip() or "No details"
                    print(f"Error fetching metrics: {msg}")

                    # If JSON body is empty then it is a graceful empty, so return {}
                    if err_json == {}:
                        return {}

                    # If JSON body has content, failure, return []
                    return []
                except Exception:
                    # If body is not JSON, treat as failure, return []
                    print("Error fetching metrics: No details")
                    return []

            return r.json()

        except Exception as e:
            print(f"[GitHub] Exception during API call: {e}")
            time.sleep(delay)

    # After retries, still processing or repeated failure
    print(f"[GitHub] Warning: API did not return data after {retries} retries. URL: {url}")
    return {}

def paginated_gh_get(token, base_url):
    page = 1
    results = []

    while True:
        sep = "&" if "?" in base_url else "?"
        url = f"{base_url}{sep}per_page=100&page={page}"

        data = gh_get(token, url)

        if not data or isinstance(data, dict):
            break

        results.extend(data)

        if len(data) < 100:
            break

        page += 1

    return results

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

    login = data.get("login")
    name = data.get("name")
    email = data.get("email")

    if not name or not str(name).strip():
        name = login # sets the name to be the username if unavailable

    if email is None:
        email = "" # avoid null

    return {
        "login": login,
        "id": data.get("id"),
        "name": name,
        "email": email,
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
        if data is None: return {"processing": True}

        # no morepages
        if isinstance(data, list) and len(data) == 0: break

        for commit in data:
            date_str = commit["commit"]["author"]["date"].split("T")[0]
            daily[date_str] += 1

        page += 1

    return dict(daily)

# gets PRs and issues, so aggregate this function to only get issues
def get_gh_repo_issues(token, owner, repo, github_username, all_issue_comments):
    page = 1
    opened = defaultdict(int)
    closed = defaultdict(int)

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page={page}"
        data = gh_get(token, url)

        if not data:
            break

        for issue in data:
            if "pull_request" in issue:
                continue

            created_at = issue.get("created_at", "").split("T")[0]
            closed_at = issue.get("closed_at")

            opened[created_at] += 1
            if closed_at:
                closed[closed_at.split("T")[0]] += 1

        if len(data) < 100:
            break

        page += 1

    # get comment counts from ALL comments
    total_issue_comments = len(all_issue_comments)
    user_issue_comments = sum(
        1 for c in all_issue_comments
        if c.get("user", {}).get("login") == github_username
    )

    return {
        "opened": dict(opened),
        "closed": dict(closed),
        "total_opened": sum(opened.values()),
        "total_closed": sum(closed.values()),
        "total_issue_comments": total_issue_comments,
        "user_issue_comments": user_issue_comments,
    }

def get_all_issue_comments(token, owner, repo):
    """
    Fetch ALL issue comments in the repository (includes PR discussion comments).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments"
    return paginated_gh_get(token, url)

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
                "number": pr.get("number"),
                "title": title,
                "body": body,
                "labels": labels,
                "created_at": created_at,
                "merged_at": merged_date,
                "state": pr.get("state"),
                "merged": bool(merged_at)
            })
        if len(data) < 100: break # break if no more pages

        page += 1

    return {
        "opened": dict(opened),
        "merged": dict(merged),
        "total_opened": sum(opened.values()),
        "total_merged": sum(merged.values()),
        "user_prs": user_prs
    }        

def get_gh_repo_contributions(token, owner, repo, github_username):
    """
    Return user commit stats AND team-wide additions/deletions.
    Keeps all your existing error handling.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
        
    # Retry locally because GitHub sometimes returns {"message":"202"}
    for _ in range(6):
        data = gh_get(token, url)

        # Still processing: gh_get returned None (HTTP 202)
        # OR payload contains "message": "202"
        if data is None or (isinstance(data, dict) and data.get("message") == "202"):
            time.sleep(1)
            continue

        break

    # After retries, might still not ready
    if data is None or (isinstance(data, dict) and data.get("message") == "202"):
        return {"processing": True}

    user_stats = {
        "commits": 0,
        "additions": 0,
        "deletions": 0,
        "contribution_percent": 0.0
    }

    team_additions = 0
    team_deletions = 0
    total_repo_commits = 0
    user_total = 0

    for contributor in data:
        total_repo_commits += contributor.get("total", 0)

        # sum team-wide additions/deletions
        for week in contributor.get("weeks", []):
            team_additions += week.get("a", 0)
            team_deletions += week.get("d", 0)

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

    return {
        "user": user_stats,
        "team": {
            "total_commits": total_repo_commits,
            "total_additions": team_additions,
            "total_deletions": team_deletions
        }
    }

# review fetching
def get_gh_pr_reviews(token, owner, repo, pull_number):
    """
    Fetch all review events on a pull request.
    GitHub API: 
    GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    return paginated_gh_get(token, url)

def get_gh_pr_review_comments(token, owner, repo, pull_number):
    """
    Fetch review comments left on a pull request (inline code comments).
    GitHub API:
    GET /repos/{owner}/{repo}/pulls/{pull_number}/comments
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
    return paginated_gh_get(token, url)

def get_gh_reviews_for_repo(token, owner, repo, pulls):
    """
    Fetch reviews + review comments for multiple PRs.
    Returns data in a structured form for later analysis layers.
    
    pulls: list[int] of PR numbers
    """
    review_data = {}

    for pr in pulls:
        review_data[pr] = {
            "reviews": get_gh_pr_reviews(token, owner, repo, pr),
            "review_comments": get_gh_pr_review_comments(token, owner, repo, pr),
        }

    return review_data  

def get_repo_commit_timestamps(token, owner, repo):
    """
    Fetch timestamps for ALL commits in the repo.
    Returns a list of datetime objects.
    Preserves all existing gh_get error-handling semantics.
    """
    page = 1
    timestamps = []

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100&page={page}"
        data = gh_get(token, url)

        # If GitHub gives nothing or returns an error object, stop
        if not data or isinstance(data, dict): break

        for commit in data:
            ts_str = commit["commit"]["author"]["date"]  # e.g. "2024-06-01T14:22:12Z"

            # Convert ISO timestamp string into datetime
            try:
                # Remove 'Z' because Python's fromisoformat doesn't accept it
                clean = ts_str.replace("Z", "")
                ts_dt = datetime.fromisoformat(clean)
                timestamps.append(ts_dt)
            except Exception:
                # ignore malformed timestamps
                continue

        # No more pages
        if len(data) < 100:
            break

        page += 1

    return timestamps
