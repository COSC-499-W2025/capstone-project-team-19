import sqlite3
import pytest
import json

from src.integrations.github.db_repo_metrics import store_github_repo_metrics, get_github_repo_metrics
from src.integrations.github.link_repo import get_gh_repo_name_and_owner, get_github_repo_metadata
from src.integrations.github.github_analysis import fetch_github_metrics
from src.analysis.code_collaborative.code_collaborative_analysis import _enhance_with_github

# constants
USER = "u1"
PROJ = "proj"
OWNER = "me"
REPO = "repo"

# Fixtures
@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE github_repo_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            project_key INTEGER NOT NULL,
            repo_owner TEXT NOT NULL,
            repo_name TEXT NOT NULL,

            total_commits INTEGER,
            commit_days INTEGER,
            first_commit_date TEXT,
            last_commit_date TEXT,

            issues_opened INTEGER,
            issues_closed INTEGER,

            prs_opened INTEGER,
            prs_merged INTEGER,

            total_additions INTEGER,
            total_deletions INTEGER,
            contribution_percent REAL,

            team_total_commits INTEGER,
            team_total_additions INTEGER,
            team_total_deletions INTEGER,

            last_synced TEXT DEFAULT (datetime('now')),

            UNIQUE(user_id, project_key, repo_owner, repo_name)
        );
    """)

    conn.execute("""
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            display_name TEXT NOT NULL
        )
    """)
    conn.execute("INSERT INTO projects (user_id, display_name) VALUES (?, ?)", (USER, PROJ))
    conn.execute("""
        CREATE TABLE project_repos (
            user_id TEXT,
            project_key INTEGER NOT NULL,
            provider TEXT,
            repo_owner TEXT,
            repo_name TEXT,
            repo_url TEXT
        )
    """)
    return conn


# Helpers
def insert_repo(conn, user=USER, proj=PROJ, owner=OWNER, repo=REPO):
    row = conn.execute(
        "SELECT project_key FROM projects WHERE user_id=? AND display_name=?",
        (user, proj),
    ).fetchone()
    pk = row[0] if row else 1
    conn.execute(
        "INSERT INTO project_repos (user_id, project_key, provider, repo_owner, repo_name, repo_url) VALUES (?, ?, 'github', ?, ?, ?)",
        (user, pk, owner, repo, f"{owner}/{repo}"),
    )

def mock_metrics(monkeypatch, commits=2, issues=3, prs=1, contrib=5):
    monkeypatch.setattr(
        "src.integrations.github.github_analysis.get_gh_repo_commit_activity",
        lambda *a: {"2024-01-01": commits}
    )
    monkeypatch.setattr(
        "src.integrations.github.github_analysis.get_gh_repo_issues",
        lambda *a: {"total_opened": issues}
    )
    monkeypatch.setattr(
        "src.integrations.github.github_analysis.fetch_pr_collaboration_graphql",
        lambda *a: {"prs_opened": prs, "team_total_prs": prs, "team_total_reviews": 0, "user_prs": [], "reviews": {}}
    )
    monkeypatch.setattr(
        "src.integrations.github.github_analysis.get_gh_repo_contributions",
        lambda *a: {"commits": contrib}
    )

# DB tests: store & retrieve metrics
def test_store_and_get_github_metrics(conn):
    metrics = {"commits": {"2024-01-01": 3}, "issues": {"total_opened": 1}}
    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, metrics)

    result = get_github_repo_metrics(conn, USER, PROJ, OWNER, REPO)
    assert result["total_commits"] == 3
    assert result["commit_days"] == 1
    assert result["first_commit_date"] == "2024-01-01"
    assert result["last_commit_date"] == "2024-01-01"
    assert result["issues_opened"] == 1
    assert result["issues_closed"] == 0
    assert result["prs_opened"] == 0
    assert result["prs_merged"] == 0
    assert result["total_additions"] == 0
    assert result["total_deletions"] == 0

def test_update_github_metrics(conn):
    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, {
        "commits": {"2024-01-01": 1}
    })

    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, {
        "commits": {"2024-01-01": 10}
    })

    updated = get_github_repo_metrics(conn, USER, PROJ, OWNER, REPO)
    assert updated["total_commits"] == 10
    assert updated["commit_days"] == 1

def test_no_metrics_found_returns_none(conn):
    assert get_github_repo_metrics(conn, "x", "y", "a", "b") is None

# Repo owner/name lookup tests
def test_get_gh_repo_name_and_owner(conn):
    insert_repo(conn)
    owner, repo = get_gh_repo_name_and_owner(conn, USER, PROJ)
    assert owner == OWNER
    assert repo == REPO

def test_get_gh_repo_name_and_owner_none(conn):
    owner, repo = get_gh_repo_name_and_owner(conn, "none", "none")
    assert owner is None
    assert repo is None

# get_github_repo_metadata wrapper
def test_get_github_repo_metadata(monkeypatch):
    monkeypatch.setattr(
        "src.integrations.github.link_repo.get_gh_repo_metadata",
        lambda owner, repo, token: ("id123", "main")
    )

    url = f"{OWNER}/testrepo"
    result = get_github_repo_metadata(USER, PROJ, url, "TOKEN")

    assert result == (url, OWNER, "testrepo", "id123", "main")

# fetch_github_metrics aggregator
def test_fetch_github_metrics(monkeypatch):
    mock_metrics(monkeypatch)

    result = fetch_github_metrics("TOKEN", OWNER, REPO, "username")

    assert result["repository"] == f"{OWNER}/{REPO}"
    assert result["username"] == "username"
    assert result["commits"] == {"2024-01-01": 2}
    assert result["issues"] == {"total_opened": 3}
    assert result["pull_requests"]["total_opened"] == 1
    assert result["contributions"] == {"commits": 5}

# _enhance_with_github skip path
def test_enhance_with_github_skips(monkeypatch, conn):
    monkeypatch.setattr("builtins.input", lambda *a: "n")
    assert _enhance_with_github(conn, USER, PROJ, "/tmp") is None
