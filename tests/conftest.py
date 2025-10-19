import sys
import os
import sqlite3
import pytest
import db

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def shared_db(tmp_path, monkeypatch):
    """
    One shared SQLite connection per test.
    Patches BOTH db.connect() and src.main.connect to return the same connection,
    so inserts/reads are visible across app code and tests.
    """
    # Use a temporary on-disk DB to avoid ':memory:' multiple-connection quirks
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_DB_PATH", str(db_path))

    # Create a single connection and initialize schema
    conn = db.connect()
    db.init_schema(conn)

    # Patch db.connect to always return THIS connection
    monkeypatch.setattr(db, "connect", lambda db_path=None: conn)

    # Patch the already-imported connect symbol inside src.main too
    import src.main as mainmod
    monkeypatch.setattr(mainmod, "connect", lambda: conn)

    yield

    # Cleanup
    try:
        conn.close()
    finally:
        monkeypatch.delenv("APP_DB_PATH", raising=False)


@pytest.fixture
def test_user_id(shared_db):
    """
    Create and return a consistent test user for all tests.
    Uses the shared test database connection.
    """
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "test-user")
    conn.close()
    return user_id
