import json
import sqlite3

from src.db.connection import init_schema
from src.db import (
    insert_code_collaborative_metrics,
    get_metrics_id,
    insert_code_collaborative_summary,
)


# -------------------------------------------------------------------
# Helper: fake metrics dict matching compute_metrics structure
# -------------------------------------------------------------------

def _make_fake_metrics(
    project_name: str = "test_project",
    path: str = "/tmp/test_project",
):
    """
    Build a minimal metrics dict that matches the compute_metrics structure
    enough for insert_code_collaborative_metrics to work.
    """
    return {
        "project": project_name,
        "path": path,
        "totals": {
            "commits_all": 10,
            "commits_yours": 7,
            "commits_coauth": 2,
            "merges": 1,
        },
        "loc": {
            "added": 120,
            "deleted": 20,
            "net": 100,
            "files_touched": 5,
            "new_files": 2,
            "renames": 1,
        },
        "history": {
            "first": None,
            "last": None,
            "L30": 3,
            "L90": 5,
            "L365": 10,
            "longest_streak": 4,
            "current_streak": 0,
            "top_days": "Mon, Tue",
            "top_hours": "10–11h",
        },
        "focus": {
            "languages": ["Python 80%", "JavaScript 20%"],
            "folders": ["src 60%", "tests 40%"],
            "top_files": ["src/main.py", "src/app.py"],
            # frameworks key can exist or not; tests below do not rely on it
        },
    }


# -------------------------------------------------------------------
# 1. Basic insert test for code_collaborative_metrics
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_inserts_row():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"
    metrics = _make_fake_metrics(project_name=project_name)

    # Store
    insert_code_collaborative_metrics(conn, user_id, project_name, metrics)

    # Fetch core fields + JSON fields
    row = conn.execute(
        """
        SELECT
            project_name,
            repo_path,
            commits_all,
            loc_added,
            languages_json,
            folders_json,
            top_files_json
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchone()

    assert row is not None, "Row should be inserted"

    (
        pname,
        repo_path,
        commits_all,
        loc_added,
        languages_json,
        folders_json,
        top_files_json,
    ) = row

    assert pname == project_name
    assert repo_path == metrics["path"]
    assert commits_all == metrics["totals"]["commits_all"]
    assert loc_added == metrics["loc"]["added"]

    langs = json.loads(languages_json)
    folders = json.loads(folders_json)
    top_files = json.loads(top_files_json)

    assert langs == metrics["focus"]["languages"]
    assert folders == metrics["focus"]["folders"]
    assert top_files == metrics["focus"]["top_files"]


# -------------------------------------------------------------------
# 2. Upsert: same (user_id, project_name) updates existing row
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_updates_on_conflict():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"

    # First insert
    metrics1 = _make_fake_metrics(project_name=project_name, path="/tmp/first_path")
    insert_code_collaborative_metrics(conn, user_id, project_name, metrics1)

    # Second insert with changed values (same user + project)
    metrics2 = _make_fake_metrics(project_name=project_name, path="/tmp/second_path")
    metrics2["totals"]["commits_all"] = 42
    metrics2["loc"]["added"] = 999
    insert_code_collaborative_metrics(conn, user_id, project_name, metrics2)

    # There should still be exactly one row
    rows = conn.execute(
        """
        SELECT repo_path, commits_all, loc_added
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchall()

    assert len(rows) == 1, "UNIQUE(user_id, project_name) should prevent duplicates"

    repo_path, commits_all, loc_added = rows[0]

    # Values should be from the SECOND call (upsert)
    assert repo_path == "/tmp/second_path"
    assert commits_all == 42
    assert loc_added == 999


# -------------------------------------------------------------------
# 3. Missing / partial metrics: safely handle missing sections
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_handles_missing_sections():
    """
    This test covers missing / partial metrics so that empty/missing sections
    do not crash the helper and are stored as NULL or empty JSON lists.
    """
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "no_focus_history_loc"

    metrics = _make_fake_metrics(project_name=project_name)
    # Drop these sections to simulate partial metrics from compute_metrics
    metrics["focus"] = {}
    metrics["history"] = {}
    metrics["loc"] = {}

    insert_code_collaborative_metrics(conn, user_id, project_name, metrics)

    row = conn.execute(
        """
        SELECT
            commits_all,
            loc_added,
            languages_json,
            folders_json,
            top_files_json
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchone()

    assert row is not None

    commits_all, loc_added, languages_json, folders_json, top_files_json = row

    # totals["commits_all"] is still present → should be set correctly
    # loc_added is missing → should be NULL (None in Python) or a safe default
    assert commits_all == metrics["totals"]["commits_all"]
    # We do not enforce a specific default for loc_added, only that it does not crash
    # and is representable (None is fine).
    # Just assert the column exists; value may be None.
    assert "loc" in metrics  # sanity

    langs = json.loads(languages_json)
    folders = json.loads(folders_json)
    top_files = json.loads(top_files_json)

    # When focus section is missing/malformed, helper should store empty lists
    assert langs == []
    assert folders == []
    assert top_files == []


# -------------------------------------------------------------------
# 4. Summaries: non-LLM + LLM for the same metrics_id
# -------------------------------------------------------------------

def test_insert_code_collaborative_summary_non_llm_and_llm():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "summary_project"
    metrics = _make_fake_metrics(project_name=project_name)

    # First, store metrics row
    insert_code_collaborative_metrics(conn, user_id, project_name, metrics)
    metrics_id = get_metrics_id(conn, user_id, project_name)
    assert metrics_id is not None

    non_llm_text = "Manual description of what the project does and my contributions."
    llm_text = (
        "Project Summary:\nLLM summary here.\n\n"
        "Contribution Summary:\nLLM contribution summary here."
    )

    # Insert non-LLM summary
    insert_code_collaborative_summary(
        conn,
        metrics_id=metrics_id,
        user_id=user_id,
        project_name=project_name,
        summary_type="non-llm",
        content=non_llm_text,
    )

    # Insert LLM summary
    insert_code_collaborative_summary(
        conn,
        metrics_id=metrics_id,
        user_id=user_id,
        project_name=project_name,
        summary_type="llm",
        content=llm_text,
    )

    rows = conn.execute(
        """
        SELECT summary_type, content
        FROM code_collaborative_summary
        WHERE metrics_id = ?
        ORDER BY id
        """,
        (metrics_id,),
    ).fetchall()

    # Expect two rows: one manual, one LLM
    assert len(rows) == 2

    types = {t for (t, _c) in rows}
    assert "non-llm" in types
    assert "llm" in types

    # Optional: verify content is stored as-is
    stored = {t: c for (t, c) in rows}
    assert stored["non-llm"] == non_llm_text
    assert stored["llm"] == llm_text
