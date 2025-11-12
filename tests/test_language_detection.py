import pytest
import sqlite3
from src.db import init_schema 
from src.common.language_detector import detect_languages

def setup_in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT,
            file_type TEXT,
            project_name TEXT,
            extension TEXT
        );
    """)
    return conn

def insert_file(conn, user_id, project_name, file_name, file_type, extension):
    conn.execute(
        "INSERT INTO files (user_id, file_name, file_type, project_name, extension) VALUES (?, ?, ?, ?, ?)",
        (user_id, file_name, file_type, project_name, extension)
    )

# --- Tests ---

def test_detect_languages_basic():
    """Detects multiple code languages, ignores duplicates and non-code files."""
    conn = setup_in_memory_db()
    user_id = 1
    project_name = "projA"

    # Insert files
    insert_file(conn, user_id, project_name, "main.py", "code", ".py")
    insert_file(conn, user_id, project_name, "utils.py", "code", ".py")
    insert_file(conn, user_id, project_name, "index.js", "code", ".js")
    insert_file(conn, user_id, project_name, "readme.txt", "text", ".txt")  # ignored

    languages = detect_languages(conn, project_name)
    assert set(languages) == {"Python", "JavaScript"}

def test_detect_languages_empty_project():
    """Returns an empty list if the project has no code files."""
    conn = setup_in_memory_db()
    user_id = 1
    project_name = "emptyProj"

    insert_file(conn, user_id, project_name, "readme.txt", "text", ".txt")
    insert_file(conn, user_id, project_name, "notes.md", "text", ".md")

    languages = detect_languages(conn, project_name)
    assert languages == []

def test_detect_languages_unknown_extensions():
    """Ignores files with extensions that aren't mapped."""
    conn = setup_in_memory_db()
    user_id = 1
    project_name = "projUnknown"

    insert_file(conn, user_id, project_name, "script.foo", "code", ".foo")
    insert_file(conn, user_id, project_name, "code.bar", "code", ".bar")

    languages = detect_languages(conn, project_name)
    assert languages == []  # nothing recognized

def test_detect_languages_case_insensitive():
    """Handles mixed-case file extensions."""
    conn = setup_in_memory_db()
    user_id = 1
    project_name = "projCase"

    insert_file(conn, user_id, project_name, "main.PY", "code", ".PY")
    insert_file(conn, user_id, project_name, "script.Js", "code", ".Js")

    languages = detect_languages(conn, project_name)
    assert set(languages) == {"Python", "JavaScript"}

def test_detect_languages_with_extended_extensions():
    """Supports additional extensions sourced from Pygments."""
    conn = setup_in_memory_db()
    user_id = 1
    project_name = "projExtended"

    insert_file(conn, user_id, project_name, "lib.rs", "code", ".rs")
    insert_file(conn, user_id, project_name, "main.go", "code", ".go")

    languages = detect_languages(conn, project_name)
    assert "Rust" in languages
    assert "Go" in languages


