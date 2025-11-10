import pytest
from datetime import datetime
from src.google_drive.process_project_files import process_project_files, analyze_drive_file

# Mock Data & Helpers

# Fake revisions returned by our mock Google Doc analyzer
FAKE_REVISIONS = [
    {"revision_id": "rev1", "raw_text": "Hello world", "word_count": 11, "timestamp": "2025-11-09T10:00:00Z"},
    {"revision_id": "rev2", "raw_text": "Second revision", "word_count": 15, "timestamp": "2025-11-09T11:00:00Z"}
]

# Mock analyze_google_doc
def fake_analyze_google_doc(service, drive_file_id, user_email):
    return {
        "status": "analyzed",
        "revisions": FAKE_REVISIONS,
        "revision_count": len(FAKE_REVISIONS),
        "total_revision_count": 5
    }

# Mock get_project_drive_files
def fake_get_project_drive_files(conn, user_id, project_name):
    return [{"drive_file_id": "file123", "drive_file_name": "TestDoc", "mime_type": "application/vnd.google-apps.document"}]

# Fixtures
@pytest.fixture
def sqlite_conn():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE text_contribution_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        drive_file_id TEXT NOT NULL,
        revision_id TEXT NOT NULL,
        words_added INTEGER NOT NULL DEFAULT 0,
        revision_text TEXT,
        revision_timestamp TEXT NOT NULL
    );""")
    cur.execute("""
    CREATE TABLE text_contribution_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_name TEXT NOT NULL,
        drive_file_id TEXT NOT NULL,
        user_revision_count INTEGER NOT NULL DEFAULT 0,
        total_word_count INTEGER NOT NULL DEFAULT 0,
        total_revision_count INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, project_name, drive_file_id)
    );""")
    conn.commit()
    yield conn
    conn.close()

# Patch the original module
import src.google_drive.process_project_files as module
module.analyze_google_doc = fake_analyze_google_doc
module.db.get_project_drive_files = fake_get_project_drive_files

# Tests
def test_process_project_files_stores_revisions(sqlite_conn):
    process_project_files(sqlite_conn, service=None, user_id=1, project_name="proj", user_email="user@example.com")
    rows = sqlite_conn.execute("SELECT revision_id, words_added FROM text_contribution_revisions").fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "rev1"
    assert rows[1][0] == "rev2"
    summary = sqlite_conn.execute("SELECT user_revision_count, total_word_count FROM text_contribution_summary").fetchone()
    assert summary == (2, sum(rev["word_count"] for rev in FAKE_REVISIONS))

def test_analyze_drive_file_returns_expected_structure():
    result = analyze_drive_file(service=None, conn=None, user_id="user@example.com", project_name="proj",
                                drive_file_id="file123", drive_file_name="TestDoc",
                                mime_type="application/vnd.google-apps.document", user_email="user@example.com")
    assert result["status"] == "analyzed"
    assert result["revision_count"] == 2
    assert result["total_revision_count"] == 5
    assert result["revisions"][0]["revision_id"] == "rev1"
