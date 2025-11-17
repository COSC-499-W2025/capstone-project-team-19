import sqlite3
import pytest

from src.db import connect, init_schema, get_or_create_user, store_parsed_files
from src.utils.parsing import collect_file_info

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
    result = conn.execute("SELECT file_name, user_id, project_name FROM files").fetchone()
    assert result == ("example.py", user_id, None)

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

#Tests for config file handling
def test_config_files_inserted_into_config_table(conn, tmp_path):
    """Config files (e.g., requirements.txt) should be stored in config_files,
       and not in the files table."""
    cfg = tmp_path / "requirements.txt"
    cfg.write_text("flask\n")

    files_info = collect_file_info(tmp_path)
    user_id = get_or_create_user(conn, "ConfigUser")

    store_parsed_files(conn, files_info, user_id)

    # Ensure config file is NOT in files table
    file_rows = conn.execute(
        "SELECT file_name FROM files WHERE file_name = ?", ("requirements.txt",)
    ).fetchall()
    assert len(file_rows) == 0

    # Ensure config file is in config_files table
    cfg_row = conn.execute(
        "SELECT file_name, user_id, project_name FROM config_files WHERE file_name = ?", ("requirements.txt",)
    ).fetchone()
    assert cfg_row is not None
    assert cfg_row[0] == "requirements.txt"
    assert cfg_row[1] == user_id
    assert cfg_row[2] is None