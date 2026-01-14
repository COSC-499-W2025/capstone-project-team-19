"""
Tests for src/db/file_contributions.py

Tests the database layer for storing and retrieving user file contributions
in collaborative projects.
"""

import pytest
import sqlite3
from src.db.file_contributions import (
    store_file_contributions,
    get_user_contributed_files,
    get_file_contribution_stats,
    has_contribution_data,
    delete_file_contributions_for_project,
)
from src.db import init_schema


@pytest.fixture
def test_conn():
    """Create an in-memory database with schema for testing."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    yield conn
    conn.close()


def test_store_file_contributions_basic(test_conn):
    """Test storing basic file contribution data."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
    }

    store_file_contributions(test_conn, user_id=1, project_name="proj1", file_contributions=contributions)

    # Verify data was stored
    cursor = test_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_code_contributions WHERE user_id = 1")
    assert cursor.fetchone()[0] == 2


def test_store_file_contributions_replace_existing(test_conn):
    """Test that INSERT OR REPLACE updates existing contributions."""
    contributions_v1 = {
        "src/main.py": {"lines_changed": 100, "commits_count": 3},
    }
    contributions_v2 = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions_v1)
    store_file_contributions(test_conn, 1, "proj1", contributions_v2)

    # Should still have only 1 row (replaced, not duplicated)
    cursor = test_conn.cursor()
    cursor.execute("SELECT lines_changed, commits_count FROM user_code_contributions WHERE user_id = 1 AND file_path = 'src/main.py'")
    result = cursor.fetchone()
    assert result == (150, 5)


def test_get_user_contributed_files_basic(test_conn):
    """Test retrieving list of contributed files."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
        "src/config.py": {"lines_changed": 20, "commits_count": 1},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    files = get_user_contributed_files(test_conn, user_id=1, project_name="proj1")

    assert len(files) == 3
    assert "src/main.py" in files
    assert "src/utils.py" in files
    assert "src/config.py" in files


def test_get_user_contributed_files_sorted_by_lines(test_conn):
    """Test that files are returned sorted by lines changed (descending)."""
    contributions = {
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/config.py": {"lines_changed": 20, "commits_count": 1},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    files = get_user_contributed_files(test_conn, user_id=1, project_name="proj1")

    # Should be sorted by lines_changed DESC
    assert files[0] == "src/main.py"  # 150 lines
    assert files[1] == "src/utils.py"  # 80 lines
    assert files[2] == "src/config.py"  # 20 lines


def test_get_user_contributed_files_with_min_lines(test_conn):
    """Test filtering files by minimum lines changed."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
        "src/config.py": {"lines_changed": 5, "commits_count": 1},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    # Get only files with at least 50 lines changed
    files = get_user_contributed_files(test_conn, user_id=1, project_name="proj1", min_lines=50)

    assert len(files) == 2
    assert "src/main.py" in files
    assert "src/utils.py" in files
    assert "src/config.py" not in files


def test_get_user_contributed_files_empty(test_conn):
    """Test querying contributions when none exist."""
    files = get_user_contributed_files(test_conn, user_id=999, project_name="nonexistent")

    assert files == []


def test_get_file_contribution_stats_basic(test_conn):
    """Test retrieving detailed stats for all files."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    stats = get_file_contribution_stats(test_conn, user_id=1, project_name="proj1")

    assert len(stats) == 2
    assert stats["src/main.py"] == {"lines_changed": 150, "commits_count": 5}
    assert stats["src/utils.py"] == {"lines_changed": 80, "commits_count": 2}


def test_get_file_contribution_stats_empty(test_conn):
    """Test stats query when no contributions exist."""
    stats = get_file_contribution_stats(test_conn, user_id=999, project_name="nonexistent")

    assert stats == {}


def test_has_contribution_data_true(test_conn):
    """Test checking if contribution data exists - positive case."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    assert has_contribution_data(test_conn, user_id=1, project_name="proj1") is True


def test_has_contribution_data_false(test_conn):
    """Test checking if contribution data exists - negative case."""
    assert has_contribution_data(test_conn, user_id=999, project_name="nonexistent") is False


def test_delete_file_contributions_for_project(test_conn):
    """Test removing all contributions for a user + project."""
    contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)
    delete_file_contributions_for_project(test_conn, 1, "proj1")

    cursor = test_conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM user_code_contributions WHERE user_id = 1 AND project_name = 'proj1'"
    )
    assert cursor.fetchone()[0] == 0


def test_multiple_users_same_project(test_conn):
    """Test that different users can have contributions to the same project."""
    user1_contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
    }
    user2_contributions = {
        "src/utils.py": {"lines_changed": 80, "commits_count": 2},
    }

    store_file_contributions(test_conn, 1, "proj1", user1_contributions)
    store_file_contributions(test_conn, 2, "proj1", user2_contributions)

    user1_files = get_user_contributed_files(test_conn, 1, "proj1")
    user2_files = get_user_contributed_files(test_conn, 2, "proj1")

    assert user1_files == ["src/main.py"]
    assert user2_files == ["src/utils.py"]


def test_same_user_multiple_projects(test_conn):
    """Test that same user can have contributions to multiple projects."""
    proj1_contributions = {
        "src/main.py": {"lines_changed": 150, "commits_count": 5},
    }
    proj2_contributions = {
        "app/index.js": {"lines_changed": 200, "commits_count": 8},
    }

    store_file_contributions(test_conn, 1, "proj1", proj1_contributions)
    store_file_contributions(test_conn, 1, "proj2", proj2_contributions)

    proj1_files = get_user_contributed_files(test_conn, 1, "proj1")
    proj2_files = get_user_contributed_files(test_conn, 1, "proj2")

    assert proj1_files == ["src/main.py"]
    assert proj2_files == ["app/index.js"]


def test_edge_case_zero_lines_changed(test_conn):
    """Test handling files with zero lines changed (e.g., file rename only)."""
    contributions = {
        "src/renamed.py": {"lines_changed": 0, "commits_count": 1},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    files = get_user_contributed_files(test_conn, 1, "proj1")

    # Should still be included (rename is a contribution)
    assert "src/renamed.py" in files


def test_edge_case_very_large_numbers(test_conn):
    """Test handling very large line counts."""
    contributions = {
        "generated/data.json": {"lines_changed": 999999, "commits_count": 1},
    }

    store_file_contributions(test_conn, 1, "proj1", contributions)

    stats = get_file_contribution_stats(test_conn, 1, "proj1")

    assert stats["generated/data.json"]["lines_changed"] == 999999
