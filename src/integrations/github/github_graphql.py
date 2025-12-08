import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def gh_graphql(token: str, query: str, variables: dict):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        GITHUB_GRAPHQL_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables
        }
    )

    resp.raise_for_status()
    return resp.json()["data"]