import json
import sqlite3
import pytest

from src.db import init_schema
from src.db.delete_project import delete_project_everywhere


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    init_schema(c)
    c.execute(
        "INSERT INTO users (user_id, username, email) VALUES (?, ?, ?)",
        (1, "testuser", "test@example.com"),
    )
    c.commit()
    return c


@pytest.fixture()
def user_id():
    return 1


def seed_dedup_registry(conn: sqlite3.Connection, user_id: int, display_name: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (user_id, display_name) VALUES (?, ?)",
        (user_id, display_name),
    )
    pk = cur.lastrowid

    cur.execute(
        """
        INSERT INTO project_versions (project_key, upload_id, fingerprint_strict, fingerprint_loose)
        VALUES (?, ?, ?, ?)
        """,
        (pk, 123, f"{display_name}_strict_fp", f"{display_name}_loose_fp"),
    )
    vk = cur.lastrowid

    cur.execute(
        "INSERT INTO version_files (version_key, relpath, file_hash) VALUES (?, ?, ?)",
        (vk, "src/main.py", f"{display_name}_hash1"),
    )
    cur.execute(
        "INSERT INTO version_files (version_key, relpath, file_hash) VALUES (?, ?, ?)",
        (vk, "README.md", f"{display_name}_hash2"),
    )

    conn.commit()
    return int(pk), int(vk)


def seed_project(conn: sqlite3.Connection, user_id: int, name: str) -> None:
    # dedup tables
    pk, vk = seed_dedup_registry(conn, user_id, name)
    project_key = pk

    # canonical project metadata now lives on `projects`
    conn.execute(
        "UPDATE projects SET classification = ?, project_type = ? WHERE user_id = ? AND display_name = ?",
        ("individual", "code", user_id, name),
    )

    # files (versioned only: version_key required)
    conn.execute(
        """
        INSERT INTO files (
            user_id, version_key, file_name, file_path, extension, file_type,
            size_bytes, created, modified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (user_id, vk, f"{name}.py", f"src/{name}.py", ".py", "code", 10),
    )

    # project_summaries
    conn.execute(
        """
        INSERT INTO project_summaries (user_id, project_key, project_type, project_mode, summary_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, int(project_key), "code", "individual", json.dumps({"summary": name})),
    )

    # github_issues
    conn.execute(
        """
        INSERT INTO github_issues (user_id, project_key, repo_owner, repo_name, issue_title)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, project_key, "owner", "repo", f"issue {name}"),
    )

    # git_individual_metrics (minimal insert works since other cols are nullable)
    conn.execute(
        "INSERT INTO git_individual_metrics (user_id, project_key) VALUES (?, ?)",
        (user_id, project_key),
    )

    conn.commit()


def count_user_project(conn: sqlite3.Connection, user_id: int, table: str, project_name: str) -> int:
    if table == "files":
        # files is versioned only; count via project_versions -> projects
        return conn.execute(
            """
            SELECT COUNT(*)
            FROM files f
            JOIN project_versions pv ON f.version_key = pv.version_key
            JOIN projects p ON pv.project_key = p.project_key
            WHERE f.user_id = ? AND p.display_name = ?
            """,
            (user_id, project_name),
        ).fetchone()[0]
    if table in {
        "project_summaries", "project_skills", "git_individual_metrics", "user_code_contributions",
        "github_repo_metrics", "github_collaboration_profiles", "github_issues", "github_issue_comments",
        "github_pull_requests", "github_commit_timestamps", "github_pr_reviews", "github_pr_review_comments",
    }:
        # migrated tables use project_key; join through projects for name-based assertions
        return conn.execute(
            f"""
            SELECT COUNT(*)
            FROM {table} t
            JOIN projects p ON p.project_key = t.project_key
            WHERE t.user_id = ? AND p.display_name = ?
            """,
            (user_id, project_name),
        ).fetchone()[0]
    return conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE user_id=? AND project_name=?",
        (user_id, project_name),
    ).fetchone()[0]


def count_dedup(conn: sqlite3.Connection, user_id: int, display_name: str) -> tuple[int, int, int]:
    projects = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE user_id=? AND display_name=?",
        (user_id, display_name),
    ).fetchone()[0]

    versions = conn.execute(
        """
        SELECT COUNT(*)
        FROM project_versions v
        JOIN projects p ON p.project_key = v.project_key
        WHERE p.user_id=? AND p.display_name=?
        """,
        (user_id, display_name),
    ).fetchone()[0]

    files = conn.execute(
        """
        SELECT COUNT(*)
        FROM version_files vf
        JOIN project_versions v ON v.version_key = vf.version_key
        JOIN projects p ON p.project_key = v.project_key
        WHERE p.user_id=? AND p.display_name=?
        """,
        (user_id, display_name),
    ).fetchone()[0]

    return projects, versions, files


def test_delete_project_everywhere_removes_only_target_project(conn, user_id):
    project1 = "proj_one"
    project2 = "proj_other"

    seed_project(conn, user_id, project1)
    seed_project(conn, user_id, project2)

    # sanity: both exist
    assert count_user_project(conn, user_id, "files", project1) == 1
    assert count_user_project(conn, user_id, "project_summaries", project1) == 1
    assert count_user_project(conn, user_id, "github_issues", project1) == 1
    assert count_user_project(conn, user_id, "git_individual_metrics", project1) == 1
    assert count_dedup(conn, user_id, project1) == (1, 1, 2)

    assert count_user_project(conn, user_id, "files", project2) == 1
    assert count_user_project(conn, user_id, "project_summaries", project2) == 1
    assert count_user_project(conn, user_id, "github_issues", project2) == 1
    assert count_user_project(conn, user_id, "git_individual_metrics", project2) == 1
    assert count_dedup(conn, user_id, project2) == (1, 1, 2)

    # act
    delete_project_everywhere(conn, user_id, project1)

    # project1 gone
    assert count_user_project(conn, user_id, "files", project1) == 0
    assert count_user_project(conn, user_id, "project_summaries", project1) == 0
    assert count_user_project(conn, user_id, "github_issues", project1) == 0
    assert count_user_project(conn, user_id, "git_individual_metrics", project1) == 0
    assert count_dedup(conn, user_id, project1) == (0, 0, 0)

    # project2 still there
    assert count_user_project(conn, user_id, "files", project2) == 1
    assert count_user_project(conn, user_id, "project_summaries", project2) == 1
    assert count_user_project(conn, user_id, "github_issues", project2) == 1
    assert count_user_project(conn, user_id, "git_individual_metrics", project2) == 1
    assert count_dedup(conn, user_id, project2) == (1, 1, 2)