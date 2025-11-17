import os
import sqlite3
from pathlib import Path
import pytest
from src.db import connect, init_schema
from src.consent.consent import record_consent

@pytest.fixture()
def tmp_conn(tmp_path: Path):
    """Each test uses its own temporary SQLite DB file."""
    os.environ["APP_DB_PATH"] = str(tmp_path / "test.db")
    conn = connect()
    init_schema(conn)

    # Seed a default user so FK(user_id=1) is valid
    # Use INSERT OR IGNORE to be idempotent across tests
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'default', NULL);"
    )
    conn.commit()

    yield conn
    conn.close()
    os.environ.pop("APP_DB_PATH", None)

def test_store_accept(tmp_conn: sqlite3.Connection):
    """Accepted consent is stored in DB."""
    cid = record_consent(tmp_conn, "accepted")
    cur = tmp_conn.execute("SELECT status FROM consent_log WHERE consent_id=?", (cid,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "accepted"

def test_store_reject(tmp_conn: sqlite3.Connection):
    """Rejected consent is stored in DB."""
    cid = record_consent(tmp_conn, "rejected")
    cur = tmp_conn.execute("SELECT status FROM consent_log WHERE consent_id=?", (cid,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "rejected"

def test_invalid_status_raises(tmp_conn: sqlite3.Connection):
    """Invalid input raises ValueError."""
    with pytest.raises(ValueError):
        record_consent(tmp_conn, "maybe")
