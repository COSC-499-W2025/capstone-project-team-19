import json
import sqlite3

from src.db import init_schema
from src.db.delete_project import delete_project_everywhere


def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)

    conn.execute(
        "INSERT INTO users (user_id, username, email) VALUES (?, ?, ?)",
        (1, "testuser", "test@example.com"),
    )
    conn.commit()
    return conn


def _seed_dedup_registry(conn: sqlite3.Connection, user_id: int, display_name: str):
    """
    Create rows in:
      - projects
      - project_versions
      - version_files
    Returns (project_key, version_key).
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (user_id, display_name)
        VALUES (?, ?)
        """,
        (user_id, display_name),
    )
    project_key = cur.lastrowid

    cur.execute(
        """
        INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose)
        VALUES (?, ?, ?, ?)
        """,
        (project_key, 123, f"{display_name}_strict_fp", f"{display_name}_loose_fp"),
    )
    version_key = cur.lastrowid

    # version_files has (version_key, relpath, file_hash) PK, all NOT NULL
    cur.execute(
        """
        INSERT INTO version_files (version_key, relpath, file_hash)
        VALUES (?, ?, ?)
        """,
        (version_key, "src/main.py", f"{display_name}_hash1"),
    )
    cur.execute(
        """
        INSERT INTO version_files (version_key, relpath, file_hash)
        VALUES (?, ?, ?)
        """,
        (version_key, "README.md", f"{display_name}_hash2"),
    )

    conn.commit()
    return project_key, version_key


def test_delete_project_everywhere_removes_only_target_project():
    conn = _make_conn()
    user_id = 1
    project1 = "proj_one"
    project2 = "proj_other"

    cur = conn.cursor()

    # -----------------------------
    # Seed dedup registry for both
    # -----------------------------
    _seed_dedup_registry(conn, user_id, project1)
    _seed_dedup_registry(conn, user_id, project2)

    # -----------------------------
    # Two classifications (one each)
    # -----------------------------
    cur.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, "/tmp/p1.zip", "p1.zip", project1, "individual", "code"),
    )

    cur.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, "/tmp/p2.zip", "p2.zip", project2, "individual", "code"),
    )

    # -----------------------------
    # Files (one each)
    # -----------------------------
    conn.execute(
        """
        INSERT INTO files (
            user_id, file_name, file_path, extension, file_type,
            size_bytes, created, modified, project_name
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
        """,
        (user_id, "a.py", "src/a.py", ".py", "code", 10, project1),
    )
    conn.execute(
        """
        INSERT INTO files (
            user_id, file_name, file_path, extension, file_type,
            size_bytes, created, modified, project_name
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
        """,
        (user_id, "b.py", "src/b.py", ".py", "code", 20, project2),
    )

    # -----------------------------
    # Project summaries (one each)
    # -----------------------------
    conn.execute(
        """
        INSERT INTO project_summaries (user_id, project_name, project_type, project_mode, summary_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project1, "code", "individual", json.dumps({"summary": "p1"})),
    )
    conn.execute(
        """
        INSERT INTO project_summaries (user_id, project_name, project_type, project_mode, summary_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project2, "code", "individual", json.dumps({"summary": "p2"})),
    )

    # -----------------------------
    # GitHub issues (one each)
    # -----------------------------
    conn.execute(
        """
        INSERT INTO github_issues (user_id, project_name, repo_owner, repo_name, issue_title)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project1, "owner", "repo", "issue p1"),
    )
    conn.execute(
        """
        INSERT INTO github_issues (user_id, project_name, repo_owner, repo_name, issue_title)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project2, "owner", "repo", "issue p2"),
    )

    # -----------------------------
    # NEW: tables you were missing before
    # -----------------------------
    conn.execute(
        """
        INSERT INTO project_feedback (
            user_id, project_name, project_type, skill_name,
            file_name, criterion_key, criterion_label,
            expected, observed_json, suggestion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, project1, "code", "testing_and_ci",
            "", "criterion.key.1", "Criterion Label 1",
            "expected", json.dumps({"x": 1}), "suggestion"
        ),
    )
    conn.execute(
        """
        INSERT INTO project_feedback (
            user_id, project_name, project_type, skill_name,
            file_name, criterion_key, criterion_label,
            expected, observed_json, suggestion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, project2, "code", "testing_and_ci",
            "", "criterion.key.2", "Criterion Label 2",
            "expected", json.dumps({"x": 2}), "suggestion"
        ),
    )

    conn.execute(
        """
        INSERT INTO project_rankings (user_id, project_name, manual_rank)
        VALUES (?, ?, ?)
        """,
        (user_id, project1, 1),
    )
    conn.execute(
        """
        INSERT INTO project_rankings (user_id, project_name, manual_rank)
        VALUES (?, ?, ?)
        """,
        (user_id, project2, 2),
    )

    conn.execute(
        """
        INSERT INTO project_thumbnails (user_id, project_name, image_path, added_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        (user_id, project1, "/tmp/thumb1.png"),
    )
    conn.execute(
        """
        INSERT INTO project_thumbnails (user_id, project_name, image_path, added_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        (user_id, project2, "/tmp/thumb2.png"),
    )

    conn.commit()

    # -----------------------------
    # Helpers
    # -----------------------------
    def count_user_project(table: str, proj: str) -> int:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id=? AND project_name=?",
            (user_id, proj),
        ).fetchone()[0]

    def count_dedup_projects(display_name: str) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM projects WHERE user_id=? AND display_name=?",
            (user_id, display_name),
        ).fetchone()[0]

    def count_dedup_versions(display_name: str) -> int:
        return conn.execute(
            """
            SELECT COUNT(*)
            FROM project_versions v
            JOIN projects p ON p.project_key = v.project_key
            WHERE p.user_id = ? AND p.display_name = ?
            """,
            (user_id, display_name),
        ).fetchone()[0]

    def count_dedup_version_files(display_name: str) -> int:
        return conn.execute(
            """
            SELECT COUNT(*)
            FROM version_files vf
            JOIN project_versions v ON v.version_key = vf.version_key
            JOIN projects p ON p.project_key = v.project_key
            WHERE p.user_id = ? AND p.display_name = ?
            """,
            (user_id, display_name),
        ).fetchone()[0]

    # -----------------------------
    # Sanity: both exist
    # -----------------------------
    assert count_user_project("project_classifications", project1) == 1
    assert count_user_project("files", project1) == 1
    assert count_user_project("project_summaries", project1) == 1
    assert count_user_project("github_issues", project1) == 1
    assert count_user_project("project_feedback", project1) == 1
    assert count_user_project("project_rankings", project1) == 1
    assert count_user_project("project_thumbnails", project1) == 1

    assert count_dedup_projects(project1) == 1
    assert count_dedup_versions(project1) == 1
    assert count_dedup_version_files(project1) == 2

    assert count_user_project("project_classifications", project2) == 1
    assert count_user_project("files", project2) == 1
    assert count_user_project("project_summaries", project2) == 1
    assert count_user_project("github_issues", project2) == 1
    assert count_user_project("project_feedback", project2) == 1
    assert count_user_project("project_rankings", project2) == 1
    assert count_user_project("project_thumbnails", project2) == 1

    assert count_dedup_projects(project2) == 1
    assert count_dedup_versions(project2) == 1
    assert count_dedup_version_files(project2) == 2

    # -----------------------------
    # Act: delete project1 everywhere
    # -----------------------------
    delete_project_everywhere(conn, user_id, project1)

    # -----------------------------
    # Project1 rows should be gone (including dedup registry)
    # -----------------------------
    assert count_user_project("project_classifications", project1) == 0
    assert count_user_project("files", project1) == 0
    assert count_user_project("project_summaries", project1) == 0
    assert count_user_project("github_issues", project1) == 0
    assert count_user_project("project_feedback", project1) == 0
    assert count_user_project("project_rankings", project1) == 0
    assert count_user_project("project_thumbnails", project1) == 0

    assert count_dedup_projects(project1) == 0
    assert count_dedup_versions(project1) == 0
    assert count_dedup_version_files(project1) == 0

    # -----------------------------
    # Project2 rows should still be there (including dedup registry)
    # -----------------------------
    assert count_user_project("project_classifications", project2) == 1
    assert count_user_project("files", project2) == 1
    assert count_user_project("project_summaries", project2) == 1
    assert count_user_project("github_issues", project2) == 1
    assert count_user_project("project_feedback", project2) == 1
    assert count_user_project("project_rankings", project2) == 1
    assert count_user_project("project_thumbnails", project2) == 1

    assert count_dedup_projects(project2) == 1
    assert count_dedup_versions(project2) == 1
    assert count_dedup_version_files(project2) == 2