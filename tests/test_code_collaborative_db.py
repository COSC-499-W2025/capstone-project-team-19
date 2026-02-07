import json
import sqlite3

from src.db.connection import init_schema
from src.db import (
    insert_code_collaborative_metrics,
    get_metrics_id,
    insert_code_collaborative_summary,
)
from src.db.projects import get_project_key


# -------------------------------------------------------------------
# Helper: fake payload matching what _build_db_payload_from_metrics returns
# -------------------------------------------------------------------

def _make_fake_payload(
    project_name: str = "test_project",
    path: str = "/tmp/test_project",
):
    """
    Build a minimal flattened payload that matches the columns of
    code_collaborative_metrics and what insert_code_collaborative_metrics expects.
    """
    return {
        "repo_path": path,
        # totals
        "commits_all": 10,
        "commits_yours": 7,
        "commits_coauth": 2,
        "merges": 1,
        # loc
        "loc_added": 120,
        "loc_deleted": 20,
        "loc_net": 100,
        "files_touched": 5,
        "new_files": 2,
        "renames": 1,
        # history
        "first_commit_at": None,
        "last_commit_at": None,
        "commits_L30": 3,
        "commits_L90": 5,
        "commits_L365": 10,
        "longest_streak": 4,
        "current_streak": 0,
        "top_days": "Mon, Tue",
        "top_hours": "10–11h",
        # focus (already JSON)
        "languages_json": json.dumps(["Python 80%", "JavaScript 20%"]),
        "folders_json": json.dumps(["src 60%", "tests 40%"]),
        "top_files_json": json.dumps(["src/main.py", "src/app.py"]),
        "frameworks_json": json.dumps([]),
    }


# -------------------------------------------------------------------
# 1. Basic insert test for code_collaborative_metrics
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_inserts_row():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"
    payload = _make_fake_payload(project_name=project_name)

    insert_code_collaborative_metrics(conn, user_id, project_name, payload)

    pk = get_project_key(conn, user_id, project_name)
    assert pk is not None
    row = conn.execute(
        """
        SELECT
            project_key,
            repo_path,
            commits_all,
            loc_added,
            languages_json,
            folders_json,
            top_files_json
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, pk),
    ).fetchone()

    assert row is not None, "Row should be inserted"

    (
        pkey,
        repo_path,
        commits_all,
        loc_added,
        languages_json,
        folders_json,
        top_files_json,
    ) = row

    assert pkey == pk
    assert repo_path == payload["repo_path"]
    assert commits_all == payload["commits_all"]
    assert loc_added == payload["loc_added"]

    langs = json.loads(languages_json)
    folders = json.loads(folders_json)
    top_files = json.loads(top_files_json)

    assert langs == json.loads(payload["languages_json"])
    assert folders == json.loads(payload["folders_json"])
    assert top_files == json.loads(payload["top_files_json"])


# -------------------------------------------------------------------
# 2. Upsert: same (user_id, project_name) updates existing row
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_updates_on_conflict():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "test_project"

    # First insert
    payload1 = _make_fake_payload(project_name=project_name, path="/tmp/first_path")
    insert_code_collaborative_metrics(conn, user_id, project_name, payload1)

    # Second insert with changed values (same user + project)
    payload2 = _make_fake_payload(project_name=project_name, path="/tmp/second_path")
    payload2["commits_all"] = 42
    payload2["loc_added"] = 999
    insert_code_collaborative_metrics(conn, user_id, project_name, payload2)

    pk = get_project_key(conn, user_id, project_name)
    assert pk is not None
    rows = conn.execute(
        """
        SELECT repo_path, commits_all, loc_added
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, pk),
    ).fetchall()

    assert len(rows) == 1, "UNIQUE(user_id, project_key) should prevent duplicates"

    repo_path, commits_all, loc_added = rows[0]
    assert repo_path == "/tmp/second_path"
    assert commits_all == 42
    assert loc_added == 999


# -------------------------------------------------------------------
# 3. Missing / partial metrics: safely handle empty JSON lists
# -------------------------------------------------------------------

def test_insert_code_collaborative_metrics_handles_empty_focus_lists():
    """
    Covers a partial/edge case: focus lists are empty, but payload still has keys.
    """
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "no_focus_project"

    payload = _make_fake_payload(project_name=project_name)
    payload["languages_json"] = json.dumps([])
    payload["folders_json"] = json.dumps([])
    payload["top_files_json"] = json.dumps([])

    insert_code_collaborative_metrics(conn, user_id, project_name, payload)

    pk = get_project_key(conn, user_id, project_name)
    assert pk is not None
    row = conn.execute(
        """
        SELECT
            languages_json,
            folders_json,
            top_files_json
        FROM code_collaborative_metrics
        WHERE user_id = ? AND project_key = ?
        """,
        (user_id, pk),
    ).fetchone()

    assert row is not None

    languages_json, folders_json, top_files_json = row

    assert json.loads(languages_json) == []
    assert json.loads(folders_json) == []
    assert json.loads(top_files_json) == []


# -------------------------------------------------------------------
# 4. Summaries: non-LLM + LLM for the same metrics_id
# -------------------------------------------------------------------

def test_insert_code_collaborative_summary_non_llm_and_llm():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)

    user_id = 1
    project_name = "summary_project"
    payload = _make_fake_payload(project_name=project_name)

    insert_code_collaborative_metrics(conn, user_id, project_name, payload)
    metrics_id = get_metrics_id(conn, user_id, project_name)
    assert metrics_id is not None

    non_llm_text = "Manual description of what the project does and my contributions."
    llm_text = (
        "Project Summary:\nLLM summary here.\n\n"
        "Contribution Summary:\nLLM contribution summary here."
    )

    insert_code_collaborative_summary(
        conn,
        metrics_id=metrics_id,
        user_id=user_id,
        project_name=project_name,
        summary_type="non-llm",
        content=non_llm_text,
    )

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

    assert len(rows) == 2

    types = {t for (t, _c) in rows}
    assert "non-llm" in types
    assert "llm" in types

    stored = {t: c for (t, c) in rows}
    assert stored["non-llm"] == non_llm_text
    assert stored["llm"] == llm_text
