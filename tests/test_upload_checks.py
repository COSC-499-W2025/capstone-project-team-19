import sqlite3
import pytest
from src.common.upload_checks import (
    handle_existing_zip
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
    result = handle_existing_zip(conn, user_id, zip_path)
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

    result = handle_existing_zip(conn, user_id, zip_path)
    assert result == zip_path

    # Ensure the old project is deleted
    rows = conn.execute("SELECT * FROM project_classifications WHERE user_id = ?", (user_id,)).fetchall()
    assert len(rows) == 0


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

    result = handle_existing_zip(conn, user_id, zip_path)
    assert result is None

