import os
import datetime as dt
import builtins
import types
import re

import pytest

import src.analysis.code_collaborative.code_collaborative_analysis as cc
from src.db import init_schema


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
    # Initialize schema to create all tables including user_code_contributions
    init_schema(tmp_sqlite_conn)

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


    # mock frameworks so it doesn't hit DB
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
    If neither allowed path exists, we should print a message explaining
    that no .git was found and that local Git history is being skipped.
    """
    # Patch zip_paths to a zip_name that doesn't exist under zip_data_dir
    def fake_zip_paths(_zip_path):
        return (
            temp_zip_layout["zip_data_dir"],
            "nonexistent_zip",
            os.path.join(temp_zip_layout["zip_data_dir"], "nonexistent_zip"),
        )

    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    # Say "no" to "Enhance analysis with GitHub data? (y/n):"
    monkeypatch.setattr("builtins.input", lambda _="": "n")

    m = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=1,
        project_name=temp_zip_layout["project_name"],
        zip_path=temp_zip_layout["zip_path"],
    )

    assert m is None
    out = capsys.readouterr().out

    # New behavior: no "[skip]" string; instead we get these:
    assert "No .git detected for" in out
    assert "[info] Skipping local Git history analysis for this project." in out
    # Still make sure the project name appears somewhere
    assert temp_zip_layout["project_name"] in out


def test_identity_prompt_and_persist(tmp_sqlite_conn, temp_zip_layout, monkeypatch, capsys):
    """
    First-run flow: no identity yet -> prompt, save chosen author,
    then run analysis and print the card.
    """
    import os

    # Initialize schema to create all tables including user_code_contributions
    init_schema(tmp_sqlite_conn)

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

def test_portfolio_summary_keywords(tmp_sqlite_conn, temp_zip_layout, monkeypatch, capsys):
    """
    Run two collaborative CODE projects, then print one combined summary.
    Assert the summary prints with the new header and includes top keywords
    from user-provided descriptions.
    """
    import os, sys, datetime as dt
    import src.analysis.code_collaborative.code_collaborative_analysis as cc  # alias under test

    # Initialize schema to create all tables including user_code_contributions
    init_schema(tmp_sqlite_conn)

    # Make stdin look interactive so description prompt runs
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True, raising=False)

    # Two project names
    proj1 = temp_zip_layout["project_name"]            # e.g., "ProjectA"
    proj2 = f"{temp_zip_layout['project_name']}_B"     # e.g., "ProjectA_B"
    expected_names = {proj1, proj2}

    # zip paths -> fixed temp layout
    def fake_zip_paths(_zip_path):
        return (
            temp_zip_layout["zip_data_dir"],
            temp_zip_layout["zip_name"],
            os.path.join(temp_zip_layout["zip_data_dir"], temp_zip_layout["zip_name"]),
        )
    monkeypatch.setattr(cc, "zip_paths", fake_zip_paths)

    # Robust resolver: accept 5-arg signature, return a path under collaborative/<project_name>
    def _mock_resolve_repo_for_project(conn, zd, zn, pn, uid):
        # pn is already supplied; ensure str join
        return os.path.join(
            str(temp_zip_layout["zip_data_dir"]),
            str(temp_zip_layout["zip_name"]),
            str(temp_zip_layout["zip_name"]),
            "collaborative",
            str(pn),
        )
    monkeypatch.setattr(cc, "resolve_repo_for_project", _mock_resolve_repo_for_project)

    # No frameworks for simplicity
    monkeypatch.setattr(cc, "detect_frameworks", lambda *args, **kwargs: set())

    # Ensure identity table exists
    cc.ensure_user_github_table(tmp_sqlite_conn)

    # Authors found in repo
    authors = [("Me Dev", "me@example.com", 10), ("Teammate", "teammate@example.com", 8)]
    monkeypatch.setattr(cc, "collect_repo_authors", lambda _repo: authors)

    # For each project: enhance? -> "n", pick author -> "1", extra emails -> "", description -> "<text>"
    answers = iter([
        "n", "1", "", "Android grocery app with RecyclerView and cart features.",
        "n", "1", "", "System mining work artifacts; Git contributions summary."
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    # Minimal fake commits authored by me@example.com
    def _fake_commits_me(_repo):
        now = dt.datetime.now(dt.timezone.utc)
        return [
            {
                "hash": "h1",
                "author_name": "Me Dev",
                "author_email": "me@example.com",
                "authored_at": now - dt.timedelta(days=10),
                "parents": [],
                "is_merge": False,
                "subject": "init",
                "body": "",
                "files": [{"path": "src/app.py", "additions": 15, "deletions": 2, "is_binary": False}],
                "name_status": {"A": 1},
            },
            {
                "hash": "h2",
                "author_name": "Me Dev",
                "author_email": "me@example.com",
                "authored_at": now - dt.timedelta(days=5),
                "parents": [],
                "is_merge": False,
                "subject": "feature",
                "body": "",
                "files": [{"path": "src/ui/recycler.py", "additions": 30, "deletions": 5, "is_binary": False}],
                "name_status": {"M": 1},
            },
        ]
    monkeypatch.setattr(cc, "read_git_history", _fake_commits_me)

    # Analyze two separate collaborative CODE projects
    m1 = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=7,
        project_name=proj1,
        zip_path=temp_zip_layout["zip_path"],
    )
    m2 = cc.analyze_code_project(
        conn=tmp_sqlite_conn,
        user_id=7,
        project_name=proj2,
        zip_path=temp_zip_layout["zip_path"],
    )

    # Now print the combined summary
    cc.print_code_portfolio_summary()

    out = capsys.readouterr().out

    # Basic checks
    assert m1 is not None and m2 is not None
    assert "Code Collaborative Analysis Summary" in out
    # keywords should include some from the two descriptions
    assert "android" in out.lower()
    assert "grocery" in out.lower()
    # and the second description
    assert "contributions" in out.lower() or "git" in out.lower()

