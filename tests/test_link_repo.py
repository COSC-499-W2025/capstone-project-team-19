import pytest, sqlite3, builtins
from src.github_auth.link_repo import ensure_repo_link, select_and_store_repo
from src.github_auth import link_repo
from src.db import init_schema, get_or_create_user

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    conn.execute("""CREATE TABLE IF NOT EXISTS project_repos (
        user_id INTEGER, project_name TEXT, provider TEXT, repo_url TEXT
    )""")
    return conn

def test_ensure_repo_link_empty(conn):
    user = get_or_create_user(conn, "Test")
    assert ensure_repo_link(conn, user, "proj", "tok") == False

def test_ensure_repo_link_exists(conn):
    user = get_or_create_user(conn, "Test")
    conn.execute("INSERT INTO project_repos VALUES (?, ?, 'github', ?)", (user, "proj", "repo/url"))
    assert ensure_repo_link(conn, user, "proj", "tok") == True

def test_select_and_store_repo_auto(monkeypatch, conn):
    user = get_or_create_user(conn, "Timmi")
    monkeypatch.setattr(link_repo, "list_user_repos", lambda x: ["coolproj", "other"])

    inputs = iter(["y"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    select_and_store_repo(conn, user, "cool", "token")

    row = conn.execute("SELECT repo_url FROM project_repos").fetchone()
    assert "coolproj" in row[0]
