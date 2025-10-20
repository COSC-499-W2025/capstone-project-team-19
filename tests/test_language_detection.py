import pytest
import sqlite3
from src.db import init_schema 
from src.language_detector import detect_languages

@pytest.fixture
def db_path(tmp_path):
    """Create a temporary SQLite database with schema for testing."""
    db_path = tmp_path / "test_local.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.close()
    return str(db_path)


def test_single_language_project(db_path):
    # Insert a sample Python file record into the DB
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO files (user_id, file_name, file_path, extension, file_type, size_bytes, created, modified)
        VALUES (1, 'main.py', 'myproject/main.py', '.py', 'source', 1234, '2025-10-19', '2025-10-19')
    """)
    conn.commit()
    conn.close()

    # Run your detection function
    result = detect_languages(db_path)

    # Check that it correctly detects Python in 'myproject'
    assert result == {"myproject": ["Python"]}

def test_multiple_languages_in_project(db_path):
    """Test detection of multiple languages within a single project."""
    conn = sqlite3.connect(db_path)
    conn.executemany("""
        INSERT INTO files (user_id, file_name, file_path, extension, file_type, size_bytes, created, modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 'main.py', 'proj1/main.py', '.py', 'source', 1000, '2025-10-19', '2025-10-19'),
        (1, 'app.js', 'proj1/app.js', '.js', 'source', 1200, '2025-10-19', '2025-10-19'),
        (1, 'style.css', 'proj1/style.css', '.css', 'source', 800, '2025-10-19', '2025-10-19'),
    ])
    conn.commit()
    conn.close()

    result = detect_languages(db_path)

    assert set(result["proj1"]) == {"Python", "JavaScript", "CSS"}

def test_multiple_projects(db_path):
    """Test detection across multiple projects."""
    conn = sqlite3.connect(db_path)
    conn.executemany("""
        INSERT INTO files (user_id, file_name, file_path, extension, file_type, size_bytes, created, modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 'main.py', 'projectA/main.py', '.py', 'source', 1000, '2025-10-19', '2025-10-19'),
        (1, 'index.html', 'projectB/index.html', '.html', 'source', 900, '2025-10-19', '2025-10-19'),
    ])
    conn.commit()
    conn.close()

    result = detect_languages(db_path)

    assert result == {
        "projectA": ["Python"],
        "projectB": ["HTML"]
    }

def test_unknown_extension_is_ignored(db_path):
    """Files with unknown extensions should be ignored."""
    conn = sqlite3.connect(db_path)
    conn.executemany("""
        INSERT INTO files (user_id, file_name, file_path, extension, file_type, size_bytes, created, modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 'main.xyz', 'proj2/main.xyz', '.xyz', 'source', 500, '2025-10-19', '2025-10-19'),
        (1, 'main.py', 'proj2/main.py', '.py', 'source', 500, '2025-10-19', '2025-10-19')
    ])
    conn.commit()
    conn.close()

    result = detect_languages(db_path)

    assert result == {"proj2": ["Python"]}

def test_empty_database_returns_empty_dict(db_path):
    """An empty database should return an empty dictionary."""
    result = detect_languages(db_path)
    assert result == {}

def test_duplicate_files_same_language(db_path):
    """Multiple files of the same language in a project should not duplicate entries."""
    conn = sqlite3.connect(db_path)
    conn.executemany("""
        INSERT INTO files (user_id, file_name, file_path, extension, file_type, size_bytes, created, modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 'a.py', 'proj3/a.py', '.py', 'source', 1000, '2025-10-19', '2025-10-19'),
        (1, 'b.py', 'proj3/b.py', '.py', 'source', 1100, '2025-10-19', '2025-10-19'),
    ])
    conn.commit()
    conn.close()

    result = detect_languages(db_path)

    assert result == {"proj3": ["Python"]}



