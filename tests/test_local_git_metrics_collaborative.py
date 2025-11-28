import json
import sqlite3

from src.db.connection import init_schema
from src.db import store_local_git_metrics_collaborative


# -------------------------------------------------------------------
# Helper: fake metrics dict matching compute_metrics structure
# -------------------------------------------------------------------

def _make_fake_metrics(
    project_name: str = "test_project",
    path: str = "/tmp/test_project",
):
    """
    Build a minimal metrics dict that matches the compute_metrics structure
    enough for store_local_git_metrics_collaborative to work.
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
        "desc": "Test project for git metrics.",
    }


# -------------------------------------------------------------------
# 1. Basic insert test
# -------------------------------------------------------------------

def test_store_local_git_metrics_inserts_row():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"
    metrics = _make_fake_metrics(project_name=project_name)

    # Store
    store_local_git_metrics_collaborative(conn, user_id, project_name, metrics)

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
            top_files_json,
            desc
        FROM local_git_metrics_collaborative
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
        desc_text,
    ) = row

    assert pname == project_name
    assert repo_path == metrics["path"]
    assert commits_all == metrics["totals"]["commits_all"]
    assert loc_added == metrics["loc"]["added"]
    assert desc_text == metrics["desc"]

    langs = json.loads(languages_json)
    folders = json.loads(folders_json)
    top_files = json.loads(top_files_json)

    assert langs == metrics["focus"]["languages"]
    assert folders == metrics["focus"]["folders"]
    assert top_files == metrics["focus"]["top_files"]


# -------------------------------------------------------------------
# 2. Upsert: same (user_id, project_name) updates existing row
# -------------------------------------------------------------------

def test_store_local_git_metrics_updates_on_conflict():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"

    # First insert
    metrics1 = _make_fake_metrics(project_name=project_name, path="/tmp/first_path")
    store_local_git_metrics_collaborative(conn, user_id, project_name, metrics1)

    # Second insert with changed values (same user + project)
    metrics2 = _make_fake_metrics(project_name=project_name, path="/tmp/second_path")
    metrics2["totals"]["commits_all"] = 42
    metrics2["loc"]["added"] = 999
    store_local_git_metrics_collaborative(conn, user_id, project_name, metrics2)

    # There should still be exactly one row
    rows = conn.execute(
        """
        SELECT repo_path, commits_all, loc_added
        FROM local_git_metrics_collaborative
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
# 3. Optional JSON fields: safely default to empty lists
# -------------------------------------------------------------------

def test_store_local_git_metrics_handles_missing_focus_fields():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "no_focus_project"

    metrics = _make_fake_metrics(project_name=project_name)
    # Drop focus section entirely to simulate missing optional fields
    metrics["focus"] = {}

    store_local_git_metrics_collaborative(conn, user_id, project_name, metrics)

    row = conn.execute(
        """
        SELECT languages_json, folders_json, top_files_json
        FROM local_git_metrics_collaborative
        WHERE user_id = ? AND project_name = ?
        """,
        (user_id, project_name),
    ).fetchone()

    assert row is not None

    languages_json, folders_json, top_files_json = row

    langs = json.loads(languages_json)
    folders = json.loads(folders_json)
    top_files = json.loads(top_files_json)

    # When missing in metrics["focus"], helper should store empty lists
    assert langs == []
    assert folders == []
    assert top_files == []
