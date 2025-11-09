import sqlite3
import pytest
import json

from src.github.db_repo_metrics import store_github_repo_metrics, get_github_repo_metrics
from src.github.link_repo import get_gh_repo_name_and_owner, get_github_repo_metadata
from src.github.github_analysis import fetch_github_metrics
from src.code_collaborative_analysis import _enhance_with_github

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
            user_id TEXT,
            project_name TEXT,
            repo_owner TEXT,
            repo_name TEXT,
            metrics_json TEXT,
            PRIMARY KEY(user_id, project_name, repo_owner, repo_name)
        )
    """)
    conn.execute("""
        CREATE TABLE project_repos (
            user_id TEXT,
            project_name TEXT,
            provider TEXT,
            repo_owner TEXT,
            repo_name TEXT,
            repo_url TEXT
        )
    """)
    return conn

# Helpers
def insert_repo(conn, user=USER, proj=PROJ, owner=OWNER, repo=REPO):
    conn.execute("""
        INSERT INTO project_repos VALUES (?, ?, 'github', ?, ?, ?)
    """, (user, proj, owner, repo, f"{owner}/{repo}"))

def mock_metrics(monkeypatch, commits=2, issues=3, prs=1, contrib=5):
    monkeypatch.setattr(
        "src.github.github_analysis.get_gh_repo_commit_activity",
        lambda *a: {"2024-01-01": commits}
    )
    monkeypatch.setattr(
        "src.github.github_analysis.get_gh_repo_issues",
        lambda *a: {"total_opened": issues}
    )
    monkeypatch.setattr(
        "src.github.github_analysis.get_gh_repo_prs",
        lambda *a: {"total_opened": prs}
    )
    monkeypatch.setattr(
        "src.github.github_analysis.get_gh_repo_contributions",
        lambda *a: {"commits": contrib}
    )

# DB tests: store & retrieve metrics
def test_store_and_get_github_metrics(conn):
    metrics = {"commits": {"2024-01-01": 3}, "issues": {"total_opened": 1}}
    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, metrics)

    result = get_github_repo_metrics(conn, USER, PROJ, OWNER, REPO)
    assert result == metrics

def test_update_github_metrics(conn):
    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, {"v": 1})
    store_github_repo_metrics(conn, USER, PROJ, OWNER, REPO, {"v": 2})

    result = get_github_repo_metrics(conn, USER, PROJ, OWNER, REPO)
    assert result == {"v": 2}

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
        "src.github.link_repo.get_gh_repo_metadata",
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
    assert result["pull_requests"] == {"total_opened": 1}
    assert result["contributions"] == {"commits": 5}

# _enhance_with_github skip path
def test_enhance_with_github_skips(monkeypatch, conn):
    monkeypatch.setattr("builtins.input", lambda *a: "n")
    assert _enhance_with_github(conn, USER, PROJ, "/tmp") is None
