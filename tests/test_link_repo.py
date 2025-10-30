import sqlite3
import pytest
from src.github_auth.link_repo import ensure_repo_link, select_and_store_repo

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE project_repos (
            user_id TEXT,
            project_name TEXT,
            provider TEXT,
            repo_url TEXT,
            PRIMARY KEY(user_id, project_name, provider)
        )
    """)
    return conn


# ensure_repo_link

def test_ensure_repo_link_exists(conn, capsys):
    conn.execute(
        "INSERT INTO project_repos VALUES (?, ?, 'github', ?)",
        ("u1", "proj", "url123")
    )
    assert ensure_repo_link(conn, "u1", "proj", "TOKEN") is True
    out = capsys.readouterr().out
    assert "Repo already linked" in out


def test_ensure_repo_link_not_exists(conn):
    assert ensure_repo_link(conn, "u1", "proj", "TOKEN") is False


# select_and_store_repo

def test_select_and_store_auto_accept(monkeypatch, conn, capsys):
    # Fake repos returned
    monkeypatch.setattr(
        "src.github_auth.link_repo.list_user_repos",
        lambda token: ["proj-one", "other"]
    )
    # Simulate user accepts auto match
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "proj-one"
    assert "Best repo match" in capsys.readouterr().out


def test_select_and_store_auto_reject_then_manual(monkeypatch, conn):
    monkeypatch.setattr(
        "src.github_auth.link_repo.list_user_repos",
        lambda token: ["proj-one", "other"]
    )

    # First reject auto match ("n"), then select option 2
    inputs = iter(["n", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "other"


def test_select_and_store_manual_only(monkeypatch, conn):
    monkeypatch.setattr(
        "src.github_auth.link_repo.list_user_repos",
        lambda token: ["alpha", "beta"]
    )
    # No auto match, choose repo #2
    monkeypatch.setattr("builtins.input", lambda prompt="": "2")

    select_and_store_repo(conn, "u1", "zzz", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "beta"


def test_select_and_store_no_repos(monkeypatch, conn, capsys):
    monkeypatch.setattr(
        "src.github_auth.link_repo.list_user_repos",
        lambda token: []
    )

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    out = capsys.readouterr().out
    assert "No repos" in out
    assert conn.execute("SELECT * FROM project_repos").fetchone() is None


def test_manual_invalid_selection(monkeypatch, conn, capsys):
    monkeypatch.setattr(
        "src.github_auth.link_repo.list_user_repos",
        lambda token: ["foo", "bar"]
    )

    # invalid input then valid
    inputs = iter(["5", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "bar"

    out = capsys.readouterr().out
    assert "Invalid" in out
