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
    checks the happy path: repo is found, identity already exists, mocked git history is used,
    and the printed card shows the right numbers.
    """
    def fake_zip_paths(_zip_path):
        return (
            temp_zip_layout["zip_data_dir"],
            temp_zip_layout["zip_name"],
            os.path.join(temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"]),
        )
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    monkeypatch.setattr(
        cc,
        "resolve_repo_for_project",
        lambda *args, **kwargs: os.path.join(
            temp_zip_layout["zip_data_dir"],
            temp_zip_layout["zip_name"],
            temp_zip_layout["zip_name"],
            "collaborative",
            temp_zip_layout["project_name"],
        ),
    )


    # mock frameworks so it doesn’t hit DB
    monkeypatch.setattr(cc, "detect_frameworks", lambda *args, **kwargs: set())

    cc.ensure_user_github_table(tmp_sqlite_conn)
    tmp_sqlite_conn.execute(
        "INSERT INTO user_github (user_id, email, name) VALUES (?,?,?)",
        (1, "me@example.com", "Me Dev"),
    )
    tmp_sqlite_conn.commit()

    monkeypatch.setattr(cc, "read_git_history", lambda _repo: _fake_commits())
    monkeypatch.setattr("builtins.input", lambda _="": "n")

    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=1,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    out = capsys.readouterr().out
    assert m is not None
    assert f"Project: {temp_zip_layout['project_name']}" in out
    assert "You: 2" in out
    assert "Commits: 3" in out
    assert "Lines: +140 / -30  →  Net +110" in out
    assert "Path:" not in out
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

    monkeypatch.setattr("builtins.input", lambda _="": "n")

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
    First-run flow: no identity yet -> prompt, save chosen author,
    then run analysis and print the card.
    """
    import os

    # zip paths -> fixed temp layout
    def fake_zip_paths(_zip_path):
        return (
            temp_zip_layout["zip_data_dir"],
            temp_zip_layout["zip_name"],
            os.path.join(temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"]),
        )
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    # repo resolver -> point to collaborative/<project_name>
    monkeypatch.setattr(
        cc,
        "resolve_repo_for_project",
        lambda *args, **kwargs: os.path.join(
            temp_zip_layout["zip_data_dir"],
            temp_zip_layout["zip_name"],
            temp_zip_layout["zip_name"],
            "collaborative",
            temp_zip_layout["project_name"],
        ),
    )

    # frameworks off
    monkeypatch.setattr(cc, "detect_frameworks", lambda *args, **kwargs: set())

    cc.ensure_user_github_table(tmp_sqlite_conn)

    # authors found in repo
    authors = [("Me Dev", "me@example.com", 10), ("Teammate", "teammate@example.com", 8)]
    monkeypatch.setattr(cc, "collect_repo_authors", lambda _repo: authors)

    # robust input mock: provide three answers; return "" if more prompts appear
    answers = iter(["n", "1", ""])  # enhance? -> n, pick author -> 1, extra emails -> ""
    def safe_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration:
            return ""  # fallback for unexpected extra prompt(s), e.g., description
    monkeypatch.setattr("builtins.input", safe_input)

    # commits authored by me@example.com
    monkeypatch.setattr(cc, "read_git_history", lambda _repo: _fake_commits("me@example.com"))

    # run
    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=7,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    # assert
    out = capsys.readouterr().out
    assert m is not None
    assert "Saved your identity for future runs" in out

    rows = tmp_sqlite_conn.execute(
        "SELECT email, name FROM user_github WHERE user_id = ?", (7,)
    ).fetchall()
    assert any(r[0] == "me@example.com" for r in rows)
    assert "You: 2" in out
