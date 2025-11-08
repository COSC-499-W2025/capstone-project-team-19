# src/github_auth/link_repo.py

from .github_api import list_user_repos, get_gh_repo_metadata
from .token_store import save_github_token, get_github_token
from src.db import connect, save_project_repo
import sqlite3

"""
GitHub repository linking utilities.

Supports associating a local project entry in the database with a GitHub repository (chosen by user).
Retrieves the user's GitHub repositories by using their stored OAuth token
It attempts to match a repo to a project automatically based on project name, otherwise it prompts the user to choose a repo
The matched/selected repo URL is saved tot he database
"""


def ensure_repo_link(conn, user_id, project_name, token):
    """
    Check if repo already linked; if yes return True,
    if no return False so user can trigger selection.
    """
    row = conn.execute("""
        SELECT repo_url FROM project_repos
        WHERE user_id=? AND project_name=? AND provider='github'
        LIMIT 1
    """, (user_id, project_name)).fetchone()

    if row:
        print(f"Repo already linked for {project_name}: {row[0]}")
        return True

    return False


def select_and_store_repo(conn, user_id, project_name, token):
    print(f"\nFetching your GitHub repos to link with project: {project_name} ...")

    repos = list_user_repos(token)

    if not repos:
        print("No repos returned from GitHub.")
        return

    # Try automatic matching
    auto = [r for r in repos if project_name.lower() in r.lower()]

    if auto:
        guess = auto[0]
        print(f"\nBest repo match: {guess}")
        ans = input("Use this repo? (y/n): ").strip().lower()
        if ans.startswith("y"):
            repo_url, repo_owner, repo_name, repo_id, default_branch = get_github_repo_metadata(user_id, project_name, guess, token)
            save_project_repo(conn, user_id, project_name, repo_url, guess, repo_owner, repo_name, repo_id, default_branch)
            return

    # Manual selection
    print("\nSelect a repo:")
    for i, r in enumerate(repos, start=1):
        print(f"{i}) {r}")

    print("\nPress Enter to skip linking a repo for this project.")

    while True:
        choice = input("\nEnter number: ").strip()

        if choice == "":
            print(f"[skip] No GitHub repo linked for {project_name}")
            return

        if choice.isdigit() and 1 <= int(choice) <= len(repos):
            repo = repos[int(choice) - 1]
            repo_url, repo_owner, repo_name, repo_id, default_branch = get_github_repo_metadata(user_id, project_name, repo, token)
            save_project_repo(conn, user_id, project_name, repo_url, choice, repo_owner, repo_name, repo_id, default_branch)
            return
        print("Invalid selection.")


def _store_repo(conn, user_id, project_name, repo_url):
    conn.execute("""
        INSERT OR REPLACE INTO project_repos (user_id, project_name, provider, repo_url)
        VALUES (?, ?, 'github', ?)
    """, (user_id, project_name, repo_url))
    
    conn.commit()
    print(f"Linked {project_name} → {repo_url}")

def get_github_repo_metadata(user_id, project_name, repo_url, token):
    # parse url for repo_owner and repo_name
    print("repo_url:", repo_url)
    repo_parts = repo_url.split("/")
    repo_owner = repo_parts[0]
    repo_name = repo_parts[1]

    repo_id, default_branch = get_gh_repo_metadata(repo_owner, repo_name, token)

    return repo_url, repo_owner, repo_name, repo_id, default_branch
