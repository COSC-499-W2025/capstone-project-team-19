import sqlite3
import pytest

from src.db import connect, init_schema, get_or_create_user, store_parsed_files
from src.parsing import collect_file_info

@pytest.fixture
def conn(tmp_path):
    # Creates a fresh SQLite DB for each test

    db_path = tmp_path / "test_local.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    yield conn
    conn.close()

def test_files_table_created(conn):
    tables = [t[0] for t in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )]
    assert "files" in tables

def test_stored_parsed_files_inserts_rows(conn, tmp_path):
    # Ensures parsed files are inserted into the database correctly

    # creating test parsed file info
    tmp_file = tmp_path / "example.py"
    tmp_file.write_text("print('The Wall was released in 1979')")

    files_info = collect_file_info(tmp_path)
    user_id = get_or_create_user(conn, "PinkFloyd")

    # insert parsed metadata into the DB
    store_parsed_files(conn, files_info, user_id)

    # verify result
    result = conn.execute("SELECT file_name, user_id FROM files").fetchone()
    assert result == ("example.py", user_id)

def test_files_linked_to_correct_user(conn, tmp_path):
    # Checks that inserted files are linked to the right user

    user1 = get_or_create_user(conn, "PinkFloyd")
    user2 = get_or_create_user(conn, "Staind")

    tmp_file = tmp_path / "main.py"
    tmp_file.write_text("print('Break the Cycle was released in 2001')")
    files_info = collect_file_info(tmp_path)

    store_parsed_files(conn, files_info, user2)
    db_user_id = conn.execute("SELECT user_id FROM files").fetchone()[0]

    assert db_user_id == user2
