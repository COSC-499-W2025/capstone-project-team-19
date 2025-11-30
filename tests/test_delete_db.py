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


def test_delete_project_everywhere_removes_only_target_project():
    conn = _make_conn()
    user_id = 1
    project1 = "proj_one"
    project2 = "proj_other"

    cur = conn.cursor()

    # Two classifications
    cur.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, "/tmp/p1.zip", "p1.zip", project1, "individual", "code"),
    )
    class_id1 = cur.lastrowid

    cur.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, "/tmp/p2.zip", "p2.zip", project2, "individual", "code"),
    )
    class_id2 = cur.lastrowid

    # Attach some data to each project

    # Files
    conn.execute(
        """
        INSERT INTO files (user_id, file_name, file_path, extension, file_type,
                           size_bytes, created, modified, project_name)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
        """,
        (user_id, "a.py", "src/a.py", ".py", "code", 10, project1),
    )
    conn.execute(
        """
        INSERT INTO files (user_id, file_name, file_path, extension, file_type,
                           size_bytes, created, modified, project_name)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
        """,
        (user_id, "b.py", "src/b.py", ".py", "code", 20, project2),
    )

    # Project summaries
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

    # GitHub issues
    conn.execute(
        """
        INSERT INTO github_issues (
            user_id, project_name, repo_owner, repo_name, issue_title
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project1, "owner", "repo", "issue p1"),
    )
    conn.execute(
        """
        INSERT INTO github_issues (
            user_id, project_name, repo_owner, repo_name, issue_title
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project2, "owner", "repo", "issue p2"),
    )

    conn.commit()

    # Sanity: rows for both projects exist
    def count(table, proj):
        return conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id=? AND project_name=?",
            (user_id, proj),
        ).fetchone()[0]

    assert count("project_classifications", project1) == 1
    assert count("files", project1) == 1
    assert count("project_summaries", project1) == 1
    assert count("github_issues", project1) == 1

    assert count("project_classifications", project2) == 1
    assert count("files", project2) == 1
    assert count("project_summaries", project2) == 1
    assert count("github_issues", project2) == 1

    # Act: delete project1 everywhere
    delete_project_everywhere(conn, user_id, project1)

    # Project1 rows should be gone
    assert count("project_classifications", project1) == 0
    assert count("files", project1) == 0
    assert count("project_summaries", project1) == 0
    assert count("github_issues", project1) == 0

    # Project2 rows should still be there
    assert count("project_classifications", project2) == 1
    assert count("files", project2) == 1
    assert count("project_summaries", project2) == 1
    assert count("github_issues", project2) == 1
