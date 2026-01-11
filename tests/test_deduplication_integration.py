import sqlite3
import pytest
from pathlib import Path
from src.utils.deduplication.integration import handle_dedup_result, run_deduplication_for_projects
from src.db.deduplication import insert_project, insert_project_version

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE projects (project_key INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT)")
    conn.execute("""CREATE TABLE project_versions (
        version_key INTEGER PRIMARY KEY AUTOINCREMENT, project_key INTEGER, upload_id INTEGER,
        fingerprint_strict TEXT, fingerprint_loose TEXT)""")
    conn.execute("CREATE TABLE version_files (version_key INTEGER, relpath TEXT, file_hash TEXT, PRIMARY KEY (version_key, relpath))")
    return conn

def test_handle_dedup_result_duplicate(conn, monkeypatch):
    pk = insert_project(conn, 1, "Existing")
    result = {"kind": "duplicate", "project_key": pk, "version_key": 1}
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert handle_dedup_result(conn, 1, result, "New") is None
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert handle_dedup_result(conn, 1, result, "New") == "New"

def test_handle_dedup_result_new_version(conn):
    pk = insert_project(conn, 1, "Existing")
    result = {"kind": "new_version", "project_key": pk, "version_key": 1}
    assert handle_dedup_result(conn, 1, result, "New") == "Existing"

def test_handle_dedup_result_new_project(conn):
    result = {"kind": "new_project", "project_key": 1, "version_key": 1}
    assert handle_dedup_result(conn, 1, result, "New") == "New"

def test_handle_dedup_result_ask(conn):
    pk = insert_project(conn, 1, "Existing")
    result = {"kind": "ask", "best_match_project_key": pk, "similarity": 0.5}
    assert handle_dedup_result(conn, 1, result, "New") == "New"

def test_run_deduplication_for_projects_empty_layout(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE projects (project_key INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT)")
    conn.execute("CREATE TABLE project_versions (version_key INTEGER PRIMARY KEY AUTOINCREMENT, project_key INTEGER, upload_id INTEGER, fingerprint_strict TEXT, fingerprint_loose TEXT)")
    conn.execute("CREATE TABLE version_files (version_key INTEGER, relpath TEXT, file_hash TEXT, PRIMARY KEY (version_key, relpath))")
    
    layout = {"root_name": None, "auto_assignments": {}, "pending_projects": []}
    skipped = run_deduplication_for_projects(conn, 1, str(tmp_path), layout)
    assert skipped == set()

def test_run_deduplication_for_projects_missing_directory(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE projects (project_key INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT)")
    conn.execute("CREATE TABLE project_versions (version_key INTEGER PRIMARY KEY AUTOINCREMENT, project_key INTEGER, upload_id INTEGER, fingerprint_strict TEXT, fingerprint_loose TEXT)")
    conn.execute("CREATE TABLE version_files (version_key INTEGER, relpath TEXT, file_hash TEXT, PRIMARY KEY (version_key, relpath))")
    
    layout = {"root_name": None, "auto_assignments": {}, "pending_projects": ["Nonexistent"]}
    skipped = run_deduplication_for_projects(conn, 1, str(tmp_path), layout)
    assert skipped == set()
