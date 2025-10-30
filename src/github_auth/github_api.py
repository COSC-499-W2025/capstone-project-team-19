import requests

"""
Takes GitHub OAuth token as input
Makes authenticated API requests
Returns a sorted, deduplicated list of repositories attached to the user's GitHub account
"""

def list_user_repos(token):
    headers = {"Authorization": f"Bearer {token}"}
    repos = []

    # Personal repos
    r = requests.get("https://api.github.com/user/repos?per_page=200", headers=headers)
    if r.status_code == 200:
        repos += [repo["full_name"] for repo in r.json()]

    # Organizations the user is in
    orgs_resp = requests.get("https://api.github.com/user/orgs", headers=headers)
    if orgs_resp.status_code == 200:
        orgs = [org["login"] for org in orgs_resp.json()]

        # For each org, fetch repos where user has push access
        for org in orgs:
            org_repos_resp = requests.get(
                f"https://api.github.com/orgs/{org}/repos?per_page=200",
                headers=headers
            )
            if org_repos_resp.status_code == 200:
                for repo in org_repos_resp.json():
                    if repo.get("permissions", {}).get("push"):
                        repos.append(repo["full_name"])

    deduplicated = {}
    for r in repos:
        key = r.lower()
        if key not in deduplicated:
            deduplicated[key] = r

    # Deduplicate and sort
    return sorted(deduplicated.values(), key=lambda s: s.lower())
