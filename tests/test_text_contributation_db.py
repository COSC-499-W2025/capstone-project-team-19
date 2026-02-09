import pytest
import sqlite3
from datetime import datetime, UTC
from src.db import store_text_contribution_revision, store_text_contribution_summary

# Fixture
@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE text_contribution_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            drive_file_id TEXT NOT NULL,
            revision_id TEXT NOT NULL,
            words_added INTEGER NOT NULL DEFAULT 0,
            revision_text TEXT,
            revision_timestamp TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE text_contribution_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_key INTEGER NOT NULL,
            drive_file_id TEXT NOT NULL,
            user_revision_count INTEGER NOT NULL DEFAULT 0,
            total_word_count INTEGER NOT NULL DEFAULT 0,
            total_revision_count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, project_key, drive_file_id)
        );
    """)
    # One project for tests
    cur.execute("INSERT INTO projects (user_id, display_name) VALUES (1, 'proj1')")
    conn.commit()
    yield conn
    conn.close()

#  Helpers
def insert_revision(conn, **kwargs):
    ts = kwargs.get("revision_timestamp", datetime.now(UTC))
    revision = {
        "user_id": kwargs["user_id"],
        "drive_file_id": kwargs["drive_file_id"],
        "revision_id": kwargs["revision_id"],
        "words_added": kwargs.get("words_added", 0),
        "revision_text": kwargs.get("revision_text"),
        "revision_timestamp": ts,
    }
    store_text_contribution_revision(conn, revision)

def insert_summary(conn, **kwargs):
    summary = {
        "user_id": kwargs["user_id"],
        "project_key": kwargs["project_key"],
        "drive_file_id": kwargs["drive_file_id"],
        "user_revision_count": kwargs.get("user_revision_count", 0),
        "total_word_count": kwargs.get("total_word_count", 0),
        "total_revision_count": kwargs.get("total_revision_count", 0),
    }
    store_text_contribution_summary(conn, summary)

def fetch_one(conn, table, **filters):
    query = f"SELECT * FROM {table} WHERE " + " AND ".join(f"{k}=?" for k in filters)
    return conn.execute(query, tuple(filters.values())).fetchone()

#  Tests
def test_insert_revision(conn):
    insert_revision(conn, user_id=1, drive_file_id="file123", revision_id="rev1", words_added=50, revision_text="Hello")
    row = fetch_one(conn, "text_contribution_revisions", revision_id="rev1")
    assert row[1:6] == (1, "file123", "rev1", 50, "Hello")
    assert row[6] is not None  # timestamp exists

def test_insert_summary(conn):
    project_key = conn.execute("SELECT project_key FROM projects WHERE user_id=1 AND display_name='proj1'").fetchone()[0]
    insert_summary(conn, user_id=1, project_key=project_key, drive_file_id="file123",
                   user_revision_count=3, total_word_count=100, total_revision_count=5)
    row = fetch_one(conn, "text_contribution_summary", project_key=project_key)
    assert row[1:] == (1, project_key, "file123", 3, 100, 5)

def test_update_summary(conn):
    project_key = conn.execute("SELECT project_key FROM projects WHERE user_id=1 AND display_name='proj1'").fetchone()[0]
    insert_summary(conn, user_id=1, project_key=project_key, drive_file_id="file123",
                   user_revision_count=3, total_word_count=100, total_revision_count=5)
    insert_summary(conn, user_id=1, project_key=project_key, drive_file_id="file123",
                   user_revision_count=4, total_word_count=150, total_revision_count=6)
    row = fetch_one(conn, "text_contribution_summary", project_key=project_key)
    assert row[4:] == (4, 150, 6)
