import os
import datetime as dt
import builtins
import types
import re

import pytest

import src.code_collaborative_analysis as cc


def _fake_commits(author_email="me@example.com"):
    """Build a small fake history: two commits by me, one by teammate."""
    now = dt.datetime.now(dt.timezone.utc)
    return [
        {
            "hash": "a1",
            "author_name": "Me Dev",
            "author_email": author_email,
            "authored_at": now,
            "parents": [],
            "is_merge": False,
            "subject": "feat: add main",
            "body": "",
            "files": [
                {"path": "app/main.py", "additions": 100, "deletions": 20, "is_binary": False},
            ],
            "name_status": {"A": 1},
        },
        {
            "hash": "a2",
            "author_name": "Me Dev",
            "author_email": author_email,
            "authored_at": now,
            "parents": [],
            "is_merge": False,
            "subject": "refactor: utils",
            "body": "",
            "files": [
                {"path": "app/utils.py", "additions": 40, "deletions": 10, "is_binary": False},
            ],
            "name_status": {"M": 1},
        },
        {
            "hash": "b1",
            "author_name": "Teammate",
            "author_email": "teammate@example.com",
            "authored_at": now,
            "parents": [],
            "is_merge": True,
            "subject": "merge",
            "body": "",
            "files": [
                {"path": "README.md", "additions": 5, "deletions": 1, "is_binary": False},
            ],
            "name_status": {"M": 1},
        },
    ]


def test_analyze_code_project_happy_path(tmp_sqlite_conn, temp_zip_layout, monkeypatch, capsys):
    """
    - Repo exists under nested <zip_name>/<zip_name>/collaborative/<project>
    - user_github identity already present (so no prompt)
    - _read_git_history returns two authored commits
    - Card prints with correct counts and NO 'Path:' line.
    """
    # Patch zip_paths to point at our temp layout
    def fake_zip_paths(_zip_path):
        return (temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"],
                os.path.join(temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"]))
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    # Use real filesystem check
    # (our fixture already created .../<zip_name>/<zip_name>/collaborative/<project>/.git)

    # Pre-create identity so no prompt occurs
    cc._ensure_user_github_table(tmp_sqlite_conn)
    tmp_sqlite_conn.execute(
        "INSERT INTO user_github (user_id, email, name) VALUES (?,?,?)",
        (1, "me@example.com", "Me Dev"),
    )
    tmp_sqlite_conn.commit()

    # Fake git history
    monkeypatch.setattr(cc, "_read_git_history", lambda repo: _fake_commits())

    # Run
    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=1,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    assert m is not None
    out = capsys.readouterr().out

    # Key assertions
    assert "Project: " + temp_zip_layout["project_name"] in out
    assert "You: 2" in out  # two authored commits
    assert "Commits: 3" in out
    # Added 100+40 = 140, deleted 20+10 = 30, net +110
    assert "Lines: +140 / -30  →  Net +110" in out
    # No 'Path:' line should be present
    assert "Path:" not in out
    # Summary one-liner present
    assert "💡 Summary:" in out


def test_no_repo_found_prints_skip(tmp_sqlite_conn, temp_zip_layout, monkeypatch, capsys):
    """
    If neither allowed path exists, we should print a single [skip] line.
    """
    # Patch zip_paths to a zip_name that doesn't exist under zip_data_dir
    def fake_zip_paths(_zip_path):
        return (temp_zip_layout["zip_data_dir"], "nonexistent_zip",
                os.path.join(temp_zip_layout["zip_data_dir"], "nonexistent_zip"))
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=1,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    assert m is None
    out = capsys.readouterr().out
    assert "[skip]" in out
    assert temp_zip_layout["project_name"] in out


def test_identity_prompt_and_persist(tmp_sqlite_conn, temp_zip_layout, monkeypatch, capsys):
    """
    When identity table is empty:
      - we list authors, user picks one, it gets saved,
      - analyzer then proceeds and prints a card.
    """
    # Point at our temp layout
    def fake_zip_paths(_zip_path):
        return (temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"],
                os.path.join(temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"]))
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    # Ensure table exists but is empty
    cc._ensure_user_github_table(tmp_sqlite_conn)

    # Provide authors (what _collect_repo_authors would find)
    authors = [("Me Dev", "me@example.com", 10), ("Teammate", "teammate@example.com", 8)]
    monkeypatch.setattr(cc, "_collect_repo_authors", lambda _repo: authors)

    # Simulate user selecting "1" (Me Dev), then no extra emails
    inputs = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    # Git history where our selected author has 2 commits
    monkeypatch.setattr(cc, "_read_git_history", lambda repo: _fake_commits("me@example.com"))

    # Run
    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=7,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    assert m is not None
    out = capsys.readouterr().out
    # Identity saved message appears
    assert "Saved your identity for future runs" in out

    # Verify DB now has our identity
    rows = tmp_sqlite_conn.execute(
        "SELECT email, name FROM user_github WHERE user_id = ?", (7,)
    ).fetchall()
    assert ("me@example.com", None) in rows or ("me@example.com", "Me Dev") in rows

    # Card reflects "You: 2"
    assert "You: 2" in out
