import sqlite3
from datetime import datetime

from src.project_analysis import detect_project_type


# helper methods to create a test database, so the real database is not used
def setup_in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT,
            file_type TEXT,
            project_name TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE project_classifications (
            classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            classification TEXT,
            project_type TEXT,
            recorded_at TEXT
        );
    """)
    return conn


def insert_file(conn, user_id, project_name, file_type):
    conn.execute(
        "INSERT INTO files (user_id, file_name, file_type, project_name) VALUES (?, ?, ?, ?)",
        (user_id, f"{project_name}.{file_type}", file_type, project_name),
    )


def insert_classification(conn, user_id, project_name, classification):
    conn.execute(
        "INSERT INTO project_classifications (user_id, project_name, classification, recorded_at) VALUES (?, ?, ?, ?)",
        (user_id, project_name, classification, datetime.now().isoformat()),
    )


# actual tests

def test_code_only_project_updates_to_code():
    conn = setup_in_memory_db()
    user_id = 1
    insert_file(conn, user_id, "projA", "code")
    insert_classification(conn, user_id, "projA", "individual")

    detect_project_type(conn, user_id, {"projA": "individual"})

    result = conn.execute("SELECT project_type FROM project_classifications WHERE project_name='projA'").fetchone()[0]
    assert result == "code"


def test_text_only_project_updates_to_text():
    conn = setup_in_memory_db()
    user_id = 1
    insert_file(conn, user_id, "projB", "text")
    insert_classification(conn, user_id, "projB", "collaborative")

    detect_project_type(conn, user_id, {"projB": "collaborative"})

    result = conn.execute("SELECT project_type FROM project_classifications WHERE project_name='projB'").fetchone()[0]
    assert result == "text"


def test_no_files_defaults_to_null(capsys):
    conn = setup_in_memory_db()
    user_id = 1
    insert_classification(conn, user_id, "projC", "individual")

    detect_project_type(conn, user_id, {"projC": "individual"})

    output = capsys.readouterr().out
    assert "Project type left as NULL" in output

    result = conn.execute("""
        SELECT project_type
        FROM project_classifications
        WHERE project_name='projC'
    """).fetchone()[0]

    # project_type should still be NULL
    assert result is None


def test_mixed_files_prompts_user(monkeypatch):
    conn = setup_in_memory_db()
    user_id = 1
    # One code and one text file, so tghe project will return as mixed (and detect_project_type() function cannot state it is code or text)
    insert_file(conn, user_id, "projD", "code")
    insert_file(conn, user_id, "projD", "text")
    insert_classification(conn, user_id, "projD", "collaborative")

    # Simulate user typing 'c' when prompted to classify a project on whether it is code or text
    monkeypatch.setattr("builtins.input", lambda _: "c")

    detect_project_type(conn, user_id, {"projD": "collaborative"})

    result = conn.execute("SELECT project_type FROM project_classifications WHERE project_name='projD'").fetchone()[0]
    assert result == "code"