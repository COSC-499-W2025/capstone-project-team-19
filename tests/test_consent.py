import os
import sqlite3
from pathlib import Path
import pytest
from db import connect, init_schema
from consent import record_consent

@pytest.fixture()
def tmp_conn(tmp_path: Path):
    """Each test uses its own temporary DB file."""
    os.environ["APP_DB_PATH"] = str(tmp_path / "test.db")
    # print("Test DB path:", os.environ["APP_DB_PATH"])
    conn = connect()
    init_schema(conn)
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
