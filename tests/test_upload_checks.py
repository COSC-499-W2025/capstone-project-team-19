import sqlite3
import pytest
from src.upload_checks import (
    check_existing_zip,
    generate_duplicate_zip_name,
    _zip_exists,
)
from src.db import init_schema


@pytest.fixture
def setup_db():
    """Create an in-memory SQLite database with schema for testing."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    yield conn
    conn.close()


"""If no matching zip_path exists, it should return the same path."""
def test_check_existing_zip_no_duplicate(monkeypatch, setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"
    result = check_existing_zip(conn, user_id, zip_path)
    assert result == zip_path

"""If duplicate exists and user chooses overwrite, it should delete old data and return same path."""
def test_check_existing_zip_duplicate_overwrite(monkeypatch, setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"

    # Insert dummy project_classifications entry
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path, "project", "proj1", "individual"))
    conn.commit()

    # Mock user input to choose overwrite
    monkeypatch.setattr("builtins.input", lambda _: "o")

    result = check_existing_zip(conn, user_id, zip_path)
    assert result == zip_path

    # Ensure the old project is deleted
    rows = conn.execute("SELECT * FROM project_classifications WHERE user_id = ?", (user_id,)).fetchall()
    assert len(rows) == 0

"""If duplicate exists and user chooses duplicate, it should return a new unique path."""
def test_check_existing_zip_duplicate_duplicate(monkeypatch, setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"

    # Insert dummy duplicate
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path, "project", "proj1", "individual"))
    conn.commit()

    # Mock user input to choose duplicate
    monkeypatch.setattr("builtins.input", lambda _: "d")

    new_path = check_existing_zip(conn, user_id, zip_path)
    assert new_path != zip_path
    assert new_path.startswith(zip_path.replace(".zip", ""))
    assert new_path.endswith(".zip")


"""If duplicate exists and user chooses reuse, should return None."""
def test_check_existing_zip_duplicate_reuse(monkeypatch, setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"

    # Insert dummy duplicate
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path, "project", "proj1", "individual"))
    conn.commit()

    monkeypatch.setattr("builtins.input", lambda _: "r")

    result = check_existing_zip(conn, user_id, zip_path)
    assert result is None


"""Ensure generate_duplicate_zip_name produces a unique name with incrementing numbers."""
def test_generate_duplicate_zip_name_creates_unique(setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"

    # Insert first existing path
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path, "project", "proj1", "individual"))
    conn.commit()

    # Add another one to simulate a second duplicate
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path.replace(".zip", "_1.zip"), "project_1", "proj2", "individual"))
    conn.commit()

    new_name = generate_duplicate_zip_name(conn, user_id, zip_path)
    assert new_name.endswith(".zip")
    assert new_name != zip_path
    assert "_2" in new_name


"""Verify that _zip_exists returns True/False correctly."""
def test__zip_exists_true_and_false(setup_db):
    conn = setup_db
    user_id = 1
    zip_path = "C:/fake/path/project.zip"

    # Insert one
    conn.execute("""
        INSERT INTO project_classifications (user_id, zip_path, zip_name, project_name, classification, recorded_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-23T00:00:00')
    """, (user_id, zip_path, "project", "proj1", "individual"))
    conn.commit()

    assert _zip_exists(conn, user_id, zip_path) is True
    assert _zip_exists(conn, user_id, "C:/fake/path/new.zip") is False
