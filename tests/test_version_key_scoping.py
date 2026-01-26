import sqlite3


def test_get_files_with_timestamps_can_scope_by_version_key():
    from src.db.files import get_files_with_timestamps

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT,
            created TEXT,
            modified TEXT,
            file_type TEXT,
            project_name TEXT,
            version_key INTEGER
        );
        """
    )

    rows = [
        (1, "a.txt", "P/a.txt", "t0", "t1", "text", "P", 10),
        (1, "b.txt", "P/b.txt", "t0", "t2", "text", "P", 10),
        (1, "a.txt", "P/a.txt", "t0", "t3", "text", "P", 11),
    ]
    conn.executemany(
        """
        INSERT INTO files (user_id, file_name, file_path, created, modified, file_type, project_name, version_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    all_files = get_files_with_timestamps(conn, user_id=1, project_name="P")
    assert {f["modified"] for f in all_files} == {"t1", "t2", "t3"}

    v10 = get_files_with_timestamps(conn, user_id=1, project_name="P", version_key=10)
    assert [f["file_name"] for f in v10] == ["a.txt", "b.txt"]
    assert {f["modified"] for f in v10} == {"t1", "t2"}

    v11 = get_files_with_timestamps(conn, user_id=1, project_name="P", version_key=11)
    assert [f["file_name"] for f in v11] == ["a.txt"]
    assert v11[0]["modified"] == "t3"


def test_fetch_files_can_scope_by_version_key():
    from src.utils.helpers import _fetch_files

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT,
            file_path TEXT,
            project_name TEXT,
            version_key INTEGER
        );
        """
    )

    rows = [
        (1, "a.txt", "text", "P/a.txt", "P", 10),
        (1, "b.txt", "text", "P/b.txt", "P", 10),
        (1, "c.txt", "text", "P/c.txt", "P", 11),
    ]
    conn.executemany(
        """
        INSERT INTO files (user_id, file_name, file_type, file_path, project_name, version_key)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    v10 = _fetch_files(conn, user_id=1, project_name="P", only_text=True, version_key=10)
    assert [f["file_name"] for f in v10] == ["a.txt", "b.txt"]

    v11 = _fetch_files(conn, user_id=1, project_name="P", only_text=True, version_key=11)
    assert [f["file_name"] for f in v11] == ["c.txt"]


def test_run_text_pipeline_threads_version_key_to_timestamp_query(monkeypatch):
    """
    This ensures the "activity type analysis" timestamp query is version-scoped.
    We avoid touching the filesystem by monkeypatching helpers.
    """
    from src.analysis.text_individual import text_analyze as ta

    captured = {"version_key": None}

    def fake_get_files_with_timestamps(conn, user_id, project_name, version_key=None):
        captured["version_key"] = version_key
        return []

    monkeypatch.setattr(ta, "get_files_with_timestamps", fake_get_files_with_timestamps)
    monkeypatch.setattr(ta, "analyze_all_csv", lambda *a, **k: {})
    monkeypatch.setattr(ta, "print_activity", lambda *a, **k: None)
    monkeypatch.setattr(ta, "_select_main_file", lambda files_sorted, base_path: files_sorted[0])
    monkeypatch.setattr(ta, "extract_text_file", lambda *a, **k: "hello")
    monkeypatch.setattr(ta, "_load_supporting_texts", lambda *a, **k: [])
    monkeypatch.setattr(ta, "prompt_manual_summary", lambda *a, **k: "summary")
    monkeypatch.setattr(
        ta,
        "extract_text_skills",
        lambda *a, **k: {"buckets": {}, "overall_score": 0.0},
    )

    parsed_files = [
        {"file_name": "draft.txt", "file_path": "P/draft.txt", "file_type": "text"},
    ]

    ta.run_text_pipeline(
        parsed_files=parsed_files,
        zip_path="dummy.zip",
        conn=None,
        user_id=1,
        project_name="P",
        version_key=123,
        consent="rejected",
        suppress_print=False,
    )

    assert captured["version_key"] == 123

