import pytest
import os
import sqlite3
from pathlib import Path
from external_consent import get_external_consent, record_external_consent
from db import connect, init_schema


@pytest.fixture()
def tmp_conn(tmp_path: Path):
    """Each test uses its own temporary SQLite DB file."""
    os.environ["APP_DB_PATH"] = str(tmp_path / "test.db")
    conn = connect()
    init_schema(conn)  # ensures table exists
    yield conn
    conn.close()
    os.environ.pop("APP_DB_PATH", None)

def test_accept_external(tmp_conn: sqlite3.Connection, monkeypatch):
    """Checks that 'accepted' external consent is stored correctly."""
    monkeypatch.setattr("builtins.input", lambda _: "y")    # pretend user typed 'y'
    status = get_external_consent()
    assert status == "accepted"

    #Store in DB and check
    cid = record_external_consent(tmp_conn, status)
    cur = tmp_conn.execute("SELECT status FROM external_consent WHERE consent_id=?", (cid,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "accepted"

def test_reject_external(tmp_conn: sqlite3.Connection, monkeypatch):
    """Checks that 'rejected' external consent is stored correctly."""
    monkeypatch.setattr("builtins.input", lambda _: "n")  # pretend user typed 'y'
    status = get_external_consent()
    assert status == "rejected"

    # Store in DB and check
    cid = record_external_consent(tmp_conn, status)
    cur = tmp_conn.execute("SELECT status FROM external_consent WHERE consent_id=?", (cid,) )
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "rejected"


def test_invalid_input(monkeypatch):
    """Simulate invalid input first, then 'y'. Ensures the prompt loops until valid input."""
    inputs = iter(["maybe", "y"])  # first invalid, then valid
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    status = get_external_consent()
    assert status == "accepted"

def test_invalid_status_raises(tmp_conn: sqlite3.Connection):
    """Invalid input raises ValueError."""
    with pytest.raises(ValueError):
        record_external_consent(tmp_conn, "maybe")

