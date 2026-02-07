import sqlite3
from datetime import datetime

from src.project_analysis import (
    detect_project_type,
    detect_project_type_auto,
    get_individual_contributions,
    run_individual_analysis,
)
from src import constants


def setup_in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            project_name TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            classification TEXT,
            project_type TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE project_versions (
            version_key INTEGER PRIMARY KEY AUTOINCREMENT,
            project_key INTEGER NOT NULL,
            upload_id INTEGER,
            fingerprint_strict TEXT NOT NULL,
            fingerprint_loose TEXT,
            created_at TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE project_summaries (
            project_summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_key INTEGER NOT NULL,
            project_type TEXT,
            project_mode TEXT,
            summary_json TEXT,
            created_at TEXT,
            UNIQUE (user_id, project_key)
        );
    """)
    conn.execute("""
        CREATE TABLE project_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_key INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            level TEXT NOT NULL,
            score REAL NOT NULL,
            evidence_json TEXT,
            UNIQUE(user_id, project_key, skill_name)
        );
    """)
    # Minimal tables needed by send_to_analysis() loaders
    conn.execute("""
        CREATE TABLE non_llm_text (
            metrics_id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_key INTEGER UNIQUE NOT NULL,
            doc_count INTEGER,
            total_words INTEGER,
            reading_level_avg REAL,
            reading_level_label TEXT,
            keywords_json TEXT,
            summary_json TEXT,
            csv_metadata TEXT,
            generated_at TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE text_activity_contribution (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_key INTEGER UNIQUE NOT NULL,
            start_date TEXT,
            end_date TEXT,
            duration_days INTEGER,
            total_files INTEGER,
            classified_files INTEGER,
            activity_classification_json TEXT,
            timeline_json TEXT,
            activity_counts_json TEXT,
            generated_at TEXT
        );
    """)
    return conn


def insert_file(conn, user_id, project_name, file_type):
    conn.execute(
        "INSERT INTO files (user_id, file_name, file_type, project_name) VALUES (?, ?, ?, ?)",
        (user_id, f"{project_name}.{file_type}", file_type, project_name),
    )


def insert_classification(conn, user_id, project_name, classification, project_type=None):
    cur = conn.execute(
        """
        INSERT INTO projects (user_id, display_name, classification, project_type)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, project_name, classification, project_type),
    )
    project_key = cur.lastrowid
    # Seed a "latest version" so get_classification_id() (now version_key) works.
    conn.execute(
        """
        INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose, created_at)
        VALUES (?, NULL, ?, ?, ?)
        """,
        (project_key, f"{project_name}_strict_fp", f"{project_name}_loose_fp", datetime.now().isoformat()),
    )
    conn.commit()

def test_detect_project_type_auto_code_only_writes_and_returns():
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projA", "code")
    insert_classification(conn, user_id, "projA", "individual")

    result = detect_project_type_auto(conn, user_id, {"projA": "individual"})

    assert result["auto_types"] == {"projA": "code"}
    assert result["mixed_projects"] == []
    assert result["unknown_projects"] == []

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projA'"
    ).fetchone()[0]
    assert db_type == "code"


def test_detect_project_type_auto_text_only_writes_and_returns():
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projB", "text")
    insert_classification(conn, user_id, "projB", "collaborative")

    result = detect_project_type_auto(conn, user_id, {"projB": "collaborative"})

    assert result["auto_types"] == {"projB": "text"}
    assert result["mixed_projects"] == []
    assert result["unknown_projects"] == []

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projB'"
    ).fetchone()[0]
    assert db_type == "text"


def test_detect_project_type_auto_unknown_project_keeps_null_and_reports_unknown():
    conn = setup_in_memory_db()
    user_id = 1

    insert_classification(conn, user_id, "projC", "individual")

    result = detect_project_type_auto(conn, user_id, {"projC": "individual"})

    assert result["auto_types"] == {}
    assert result["mixed_projects"] == []
    assert result["unknown_projects"] == ["projC"]

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projC'"
    ).fetchone()[0]
    assert db_type is None


def test_detect_project_type_auto_mixed_project_is_returned_and_not_written():
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projD", "code")
    insert_file(conn, user_id, "projD", "text")
    insert_classification(conn, user_id, "projD", "collaborative")

    result = detect_project_type_auto(conn, user_id, {"projD": "collaborative"})

    assert result["auto_types"] == {}
    assert result["mixed_projects"] == ["projD"]
    assert result["unknown_projects"] == []

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projD'"
    ).fetchone()[0]
    assert db_type is None


def test_detect_project_type_auto_never_prompts(monkeypatch):
    """
    Guardrail: detect_project_type_auto() must be API-safe (no input()).
    """
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projA", "code")
    insert_classification(conn, user_id, "projA", "individual")

    def _boom(*args, **kwargs):
        raise AssertionError("input() should not be called in detect_project_type_auto")

    monkeypatch.setattr("builtins.input", _boom)

    result = detect_project_type_auto(conn, user_id, {"projA": "individual"})
    assert result["auto_types"]["projA"] == "code"

def test_detect_project_type_wrapper_does_not_prompt_for_unambiguous(monkeypatch):
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projA", "code")
    insert_classification(conn, user_id, "projA", "individual")

    def _boom(*args, **kwargs):
        raise AssertionError("input() should not be called for unambiguous projects")

    monkeypatch.setattr("builtins.input", _boom)

    detect_project_type(conn, user_id, {"projA": "individual"})

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projA'"
    ).fetchone()[0]
    assert db_type == "code"


def test_mixed_files_prompts_user(monkeypatch):
    conn = setup_in_memory_db()
    user_id = 1

    insert_file(conn, user_id, "projD", "code")
    insert_file(conn, user_id, "projD", "text")
    insert_classification(conn, user_id, "projD", "collaborative")

    monkeypatch.setattr("builtins.input", lambda _: "c")

    detect_project_type(conn, user_id, {"projD": "collaborative"})

    result = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projD'"
    ).fetchone()[0]
    assert result == "code"


def test_no_files_defaults_to_null():
    conn = setup_in_memory_db()
    user_id = 1

    insert_classification(conn, user_id, "projC", "individual")

    detect_project_type(conn, user_id, {"projC": "individual"})

    db_type = conn.execute(
        "SELECT project_type FROM projects WHERE display_name='projC'"
    ).fetchone()[0]
    assert db_type is None

def test_send_to_analysis_calls_correct_flows_verbose(monkeypatch, capsys):
    from src import constants
    constants.VERBOSE = True

    conn = setup_in_memory_db()
    user_id = 1

    insert_classification(conn, user_id, "projText", "individual", "text")
    insert_classification(conn, user_id, "projCode", "collaborative", "code")
    insert_classification(conn, user_id, "projNull", "individual", None)

    called = {"text": False, "collab": False}

    monkeypatch.setattr(
        "src.project_analysis.run_individual_analysis",
        lambda *a, **kw: called.__setitem__("text", True),
    )
    monkeypatch.setattr(
        "src.project_analysis.get_individual_contributions",
        lambda *a, **kw: called.__setitem__("collab", True),
    )

    answers = iter(["y", "y", "Worked on backend endpoints."])
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))

    from src.project_analysis import send_to_analysis
    send_to_analysis(
        conn,
        user_id,
        {"projText": "individual", "projCode": "collaborative", "projNull": "individual"},
        "accepted",
        "/tmp/fake.zip",
    )

    out = capsys.readouterr().out

    assert "[INDIVIDUAL] Running individual projects..." in out
    assert "  → projText (text)" in out
    assert "[COLLABORATIVE] Running collaborative projects..." in out
    assert "  → projCode (code)" in out
    assert "Skipping 'projNull'" in out

    assert called["text"]
    assert called["collab"]


def test_send_to_analysis_calls_correct_flows_non_verbose(monkeypatch, capsys):
    from src import constants
    constants.VERBOSE = False

    conn = setup_in_memory_db()
    user_id = 1

    insert_classification(conn, user_id, "projText", "individual", "text")
    insert_classification(conn, user_id, "projCode", "collaborative", "code")
    insert_classification(conn, user_id, "projNull", "individual", None)

    called = {"text": False, "collab": False}

    monkeypatch.setattr(
        "src.project_analysis.run_individual_analysis",
        lambda *a, **kw: called.__setitem__("text", True),
    )
    monkeypatch.setattr(
        "src.project_analysis.get_individual_contributions",
        lambda *a, **kw: called.__setitem__("collab", True),
    )

    answers = iter(["y", "y", "Handled API integrations."])
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))

    from src.project_analysis import send_to_analysis
    send_to_analysis(
        conn,
        user_id,
        {"projText": "individual", "projCode": "collaborative", "projNull": "individual"},
        "accepted",
        "/tmp/fake.zip",
    )

    out = capsys.readouterr().out

    assert "projText" in out
    assert "projCode" in out
    assert "[INDIVIDUAL]" not in out
    assert "[COLLABORATIVE]" not in out

    assert called["text"]
    assert called["collab"]


def test_get_individual_contributions_branches_verbose(monkeypatch, capsys, tmp_path):
    from src import constants
    constants.VERBOSE = True

    called = {"text": False, "code": False}

    from src import project_analysis as pa
    monkeypatch.setattr(pa, "analyze_text_contributions", lambda *a, **kw: called.__setitem__("text", True))
    monkeypatch.setattr(pa, "analyze_code_contributions", lambda *a, **kw: called.__setitem__("code", True))

    conn = setup_in_memory_db()
    zip_path = str(tmp_path / "file.zip")
    (tmp_path / "file.zip").write_text("")

    get_individual_contributions(conn, 1, "pA", "text", "acc", zip_path)
    get_individual_contributions(conn, 1, "pB", "code", "acc", zip_path)

    out = capsys.readouterr().out

    assert called["text"] and called["code"]
    assert "[COLLABORATIVE] Preparing contribution analysis for 'pA' (text)" in out
    assert "[COLLABORATIVE] Preparing contribution analysis for 'pB' (code)" in out


def test_get_individual_contributions_branches_non_verbose(monkeypatch, capsys, tmp_path):
    from src import constants
    constants.VERBOSE = False

    called = {"text": False, "code": False}

    from src import project_analysis as pa
    monkeypatch.setattr(pa, "analyze_text_contributions", lambda *a, **kw: called.__setitem__("text", True))
    monkeypatch.setattr(pa, "analyze_code_contributions", lambda *a, **kw: called.__setitem__("code", True))

    conn = setup_in_memory_db()
    zip_path = str(tmp_path / "file.zip")
    (tmp_path / "file.zip").write_text("")

    get_individual_contributions(conn, 1, "pA", "text", "acc", zip_path)
    get_individual_contributions(conn, 1, "pB", "code", "acc", zip_path)

    out = capsys.readouterr().out

    assert called["text"] and called["code"]
    assert "[COLLABORATIVE]" not in out
    assert "Preparing" not in out


def test_run_individual_analysis_branches(monkeypatch):
    called = {"text": False, "code": False}

    monkeypatch.setattr(
        "src.project_analysis.run_text_analysis",
        lambda *a, **kw: called.__setitem__("text", True),
    )
    monkeypatch.setattr(
        "src.project_analysis.run_code_analysis",
        lambda *a, **kw: called.__setitem__("code", True),
    )

    conn = setup_in_memory_db()

    run_individual_analysis(conn, 1, "projText", "text", "accepted", "/tmp/fake.zip")
    run_individual_analysis(conn, 1, "projCode", "code", "accepted", "/tmp/fake.zip")

    assert called["text"]
    assert called["code"]

