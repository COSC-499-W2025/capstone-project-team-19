import sqlite3
import pytest
from src.integrations.github.link_repo import ensure_repo_link, select_and_store_repo

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            display_name TEXT NOT NULL
        )
    """)
    conn.execute("INSERT INTO projects (user_id, display_name) VALUES ('u1', 'proj')")
    conn.execute("INSERT INTO projects (user_id, display_name) VALUES ('u1', 'zzz')")
    conn.execute("""
        CREATE TABLE project_repos (
            user_id TEXT,
            project_key INTEGER NOT NULL,
            provider TEXT,
            repo_url TEXT,
            PRIMARY KEY(user_id, project_key, provider)
        )
    """)
    conn.commit()
    return conn


@pytest.fixture
def mock_github_metadata(monkeypatch, conn):
    # Mock metadata lookup
    monkeypatch.setattr(
        "src.integrations.github.link_repo.get_github_repo_metadata",
        lambda user, proj, repo, token: (
            repo,
            repo.split('/')[0],
            repo.split('/')[-1],
            None,
            None
        )
    )

    # Mock save function to match test DB schema (project_key)
    def _mock_save(c, user, proj, repo_url, *args):
        row = c.execute(
            "SELECT project_key FROM projects WHERE user_id=? AND display_name=?",
            (user, proj),
        ).fetchone()
        pk = row[0] if row else None
        if pk is not None:
            c.execute(
                "INSERT OR REPLACE INTO project_repos (user_id, project_key, provider, repo_url) VALUES (?, ?, 'github', ?)",
                (user, pk, repo_url),
            )
            c.commit()

    monkeypatch.setattr(
        "src.integrations.github.link_repo.save_project_repo",
        _mock_save,
    )

    return True

@pytest.fixture
def mock_repos(monkeypatch):
    def _set(repos):
        monkeypatch.setattr(
            "src.integrations.github.link_repo.list_user_repos",
            lambda token: repos
        )
    return _set

# ensure_repo_link

def test_ensure_repo_link_exists(conn, capsys):
    conn.execute(
        "INSERT INTO project_repos (user_id, project_key, provider, repo_url) VALUES (?, ?, 'github', ?)",
        ("u1", 1, "url123"),
    )
    conn.commit()
    assert ensure_repo_link(conn, "u1", "proj", "TOKEN") is True
    out = capsys.readouterr().out
    assert "Repo already linked" in out


def test_ensure_repo_link_not_exists(conn):
    assert ensure_repo_link(conn, "u1", "proj", "TOKEN") is False


# select_and_store_repo

def test_select_and_store_auto_accept(monkeypatch, conn, capsys, mock_github_metadata, mock_repos):
    # Fake repos returned
    mock_repos(["me/proj-one", "me/other"])
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "me/proj-one"

def test_select_and_store_auto_reject_then_manual(monkeypatch, conn, mock_github_metadata, mock_repos):
    mock_repos(["me/proj-one", "me/other"])
    # First reject auto match ("n"), then select option 2
    inputs = iter(["n", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "me/other"


def test_select_and_store_manual_only(monkeypatch, conn, mock_github_metadata, mock_repos):
    mock_repos(["alpha", "beta"])
    # No auto match, choose repo #2
    monkeypatch.setattr("builtins.input", lambda prompt="": "2")

    select_and_store_repo(conn, "u1", "zzz", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "beta"


def test_select_and_store_no_repos(monkeypatch, conn, capsys, mock_github_metadata, mock_repos):
    mock_repos([])

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    out = capsys.readouterr().out
    assert "No repos" in out
    assert conn.execute("SELECT * FROM project_repos").fetchone() is None


def test_manual_invalid_selection(monkeypatch, conn, capsys, mock_github_metadata, mock_repos):
    mock_repos(["foo", "bar"])
    # invalid input then valid
    inputs = iter(["5", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    select_and_store_repo(conn, "u1", "proj", "TOKEN")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert row[0] == "bar"

    out = capsys.readouterr().out
    assert "Invalid" in out
