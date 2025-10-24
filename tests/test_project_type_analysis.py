import sqlite3
from datetime import datetime

from src.project_analysis import detect_project_type, get_individual_contributions, run_individual_analysis


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


def insert_classification(conn, user_id, project_name, classification, project_type=None):
    conn.execute(
        "INSERT INTO project_classifications (user_id, project_name, classification, project_type, recorded_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, project_name, classification, project_type, datetime.now().isoformat()),
    )

# tests for detect_project_type() function

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


# tests for send_to_analysis() function

def test_send_to_analysis_calls_correct_flows(monkeypatch, capsys):
    conn = setup_in_memory_db()
    user_id = 1

    # Insert sample projects with known types
    insert_classification(conn, user_id, "projText", "individual", "text")
    insert_classification(conn, user_id, "projCode", "collaborative", "code")
    insert_classification(conn, user_id, "projNull", "individual", None)

    # Mock the downstream functions so we can confirm routing
    called = {"text": False, "code": False, "collab": False}

    monkeypatch.setattr("src.project_analysis.run_individual_analysis", lambda *a, **kw: called.__setitem__("text", True))
    monkeypatch.setattr("src.project_analysis.get_individual_contributions", lambda *a, **kw: called.__setitem__("collab", True))

    # Run
    from src.project_analysis import send_to_analysis
    send_to_analysis(conn, user_id, {
        "projText": "individual",
        "projCode": "collaborative",
        "projNull": "individual",
    }, "accepted")

    out = capsys.readouterr().out
    assert "Running collaborative flow for projCode" in out
    assert "Running individual flow for projText" in out
    assert "Skipping 'projNull': project_type is NULL" in out
    assert called["text"]
    assert called["collab"]


# tests for routing layer (get_individual_contributions() function and run_individual_analysis() function)
def test_get_individual_contributions_branches(monkeypatch, capsys):
    called = {"text": False, "code": False}

    monkeypatch.setattr("src.project_analysis.analyze_text_contributions", lambda *a, **kw: called.__setitem__("text", True))
    monkeypatch.setattr("src.project_analysis.analyze_code_contributions", lambda *a, **kw: called.__setitem__("code", True))

    conn = setup_in_memory_db()
    get_individual_contributions(conn, 1, "projT", "text", "accepted")
    get_individual_contributions(conn, 1, "projC", "code", "accepted")

    out = capsys.readouterr().out
    assert "[COLLABORATIVE] Preparing contribution analysis" in out
    assert called["text"]
    assert called["code"]


def test_run_individual_analysis_branches(monkeypatch):
    called = {"text": False, "code": False}

    monkeypatch.setattr("src.project_analysis.run_text_analysis", lambda *a, **kw: called.__setitem__("text", True))
    monkeypatch.setattr("src.project_analysis.run_code_analysis", lambda *a, **kw: called.__setitem__("code", True))

    conn = setup_in_memory_db()
    run_individual_analysis(conn, 1, "projText", "text", "accepted")
    run_individual_analysis(conn, 1, "projCode", "code", "accepted")

    assert called["text"]
    assert called["code"]