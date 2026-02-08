import sqlite3

from src.db import init_schema


def test_get_files_with_timestamps_can_scope_by_version_key():
    from src.db.files import get_files_with_timestamps

    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    conn.execute("INSERT INTO projects (user_id, display_name) VALUES (1, 'P')")
    pk = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose) VALUES (?, 1, 'fp1', 'fp1')",
        (pk,),
    )
    vk1 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose) VALUES (?, 1, 'fp2', 'fp2')",
        (pk,),
    )
    vk2 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.executemany(
        """
        INSERT INTO files (user_id, version_key, file_name, file_path, created, modified, file_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, vk1, "a.txt", "P/a.txt", "t0", "t1", "text"),
            (1, vk1, "b.txt", "P/b.txt", "t0", "t2", "text"),
            (1, vk2, "a.txt", "P/a.txt", "t0", "t3", "text"),
        ],
    )
    conn.commit()

    # Latest version (vk2) only
    all_files = get_files_with_timestamps(conn, user_id=1, project_name="P")
    assert len(all_files) == 1 and all_files[0]["modified"] == "t3"

    v1 = get_files_with_timestamps(conn, user_id=1, project_name="P", version_key=vk1)
    assert [f["file_name"] for f in v1] == ["a.txt", "b.txt"]
    assert {f["modified"] for f in v1} == {"t1", "t2"}

    v2 = get_files_with_timestamps(conn, user_id=1, project_name="P", version_key=vk2)
    assert [f["file_name"] for f in v2] == ["a.txt"]
    assert v2[0]["modified"] == "t3"


def test_fetch_files_can_scope_by_version_key():
    from src.utils.helpers import _fetch_files

    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    conn.execute("INSERT INTO projects (user_id, display_name) VALUES (1, 'P')")
    pk = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose) VALUES (?, 1, 'fp1', 'fp1')",
        (pk,),
    )
    vk1 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose) VALUES (?, 1, 'fp2', 'fp2')",
        (pk,),
    )
    vk2 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.executemany(
        """
        INSERT INTO files (user_id, version_key, file_name, file_type, file_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(1, vk1, "a.txt", "text", "P/a.txt"), (1, vk1, "b.txt", "text", "P/b.txt"), (1, vk2, "c.txt", "text", "P/c.txt")],
    )
    conn.commit()

    v1 = _fetch_files(conn, user_id=1, project_name="P", only_text=True, version_key=vk1)
    assert [f["file_name"] for f in v1] == ["a.txt", "b.txt"]

    v2 = _fetch_files(conn, user_id=1, project_name="P", only_text=True, version_key=vk2)
    assert [f["file_name"] for f in v2] == ["c.txt"]


def test_run_text_pipeline_threads_version_key_to_timestamp_query(monkeypatch):
    """
    This ensures the "activity type analysis" timestamp query is version-scoped.
    When version_key is passed, run_text_pipeline uses get_files_with_timestamps_for_version.
    """
    from src.analysis.text_individual import text_analyze as ta

    captured = {"version_key": None}

    def fake_get_files_with_timestamps_for_version(conn, user_id, version_key):
        captured["version_key"] = version_key
        return []

    monkeypatch.setattr(ta, "get_files_with_timestamps_for_version", fake_get_files_with_timestamps_for_version)
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

