import requests

def list_user_repos(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get("https://api.github.com/user/repos", headers=headers)

    if r.status_code != 200:
        raise Exception(f"GitHub API error: {r.status_code} {r.text}")

    data = r.json()
    return [repo["full_name"] for repo in data]
