"""
tests/test_project_rankings.py

Comprehensive tests for the manual project re-ranking feature.
Tests database operations and ranking logic.
"""

import pytest
import sqlite3
import json
from dataclasses import asdict
from src.db import (
    connect,
    init_schema,
    get_or_create_user,
    get_project_rank,
    get_all_project_ranks,
    save_project_summary
)
from src.services.project_rankings_write_service import (
    bulk_set_rankings,
    clear_all_rankings,
    clear_project_rank,
    set_project_rank,
)
from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.models.project_summary import ProjectSummary


@pytest.fixture
def db_conn():
    """Create a test database connection."""
    conn = connect()
    init_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def test_user(db_conn):
    """Create a test user."""
    user_id = get_or_create_user(db_conn, "test_rank_user")
    return user_id


@pytest.fixture
def test_projects(db_conn, test_user):
    """Create test projects with summaries for ranking tests."""
    projects = [
        ("Project Alpha", "code", "individual", 0.85),
        ("Project Beta", "code", "collaborative", 0.72),
        ("Project Gamma", "text", "individual", 0.68),
        ("Project Delta", "code", "individual", 0.91),
    ]

    for project_name, project_type, project_mode, score in projects:
        # Create a minimal project summary
        summary = ProjectSummary(
            project_name=project_name,
            project_type=project_type,
            project_mode=project_mode,
            summary_text=f"Test summary for {project_name}",
            skills=["Python", "Testing"],
            metrics={"score": score}
        )
        # Convert to JSON string for save_project_summary
        summary_dict = asdict(summary)
        summary_dict['created_at'] = summary.created_at.isoformat()
        summary_json = json.dumps(summary_dict)
        save_project_summary(db_conn, test_user, project_name, summary_json)

    return projects


class TestDatabaseOperations:
    """Test all database operations for project rankings."""

    def test_set_project_rank(self, db_conn, test_user):
        """Test setting a manual rank for a project."""
        set_project_rank(db_conn, test_user, "Test Project", 1)

        rank = get_project_rank(db_conn, test_user, "Test Project")
        assert rank == 1

    def test_set_project_rank_null(self, db_conn, test_user):
        """Test setting rank to NULL (auto-ranking)."""
        set_project_rank(db_conn, test_user, "Test Project", 1)
        set_project_rank(db_conn, test_user, "Test Project", None)

        rank = get_project_rank(db_conn, test_user, "Test Project")
        assert rank is None

    def test_get_project_rank_nonexistent(self, db_conn, test_user):
        """Test getting rank for a project that doesn't have one."""
        rank = get_project_rank(db_conn, test_user, "Nonexistent Project")
        assert rank is None

    def test_get_all_project_ranks(self, db_conn, test_user):
        """Test getting all project ranks."""
        set_project_rank(db_conn, test_user, "Project A", 1)
        set_project_rank(db_conn, test_user, "Project B", 2)
        set_project_rank(db_conn, test_user, "Project C", 3)

        ranks = get_all_project_ranks(db_conn, test_user)

        assert len(ranks) == 3
        assert ranks[0] == ("Project A", 1)
        assert ranks[1] == ("Project B", 2)
        assert ranks[2] == ("Project C", 3)

    def test_get_all_project_ranks_sorted(self, db_conn, test_user):
        """Test that ranks are returned sorted."""
        # Use bulk_set_rankings to avoid automatic shifting
        bulk_set_rankings(db_conn, test_user, [
            ("Project C", 3),
            ("Project A", 1),
            ("Project B", 2),
        ])

        ranks = get_all_project_ranks(db_conn, test_user)

        # Should be sorted by rank ascending
        assert ranks[0][1] == 1
        assert ranks[1][1] == 2
        assert ranks[2][1] == 3

    def test_clear_project_rank(self, db_conn, test_user):
        """Test clearing a single project rank."""
        set_project_rank(db_conn, test_user, "Project A", 1)
        clear_project_rank(db_conn, test_user, "Project A")

        rank = get_project_rank(db_conn, test_user, "Project A")
        assert rank is None

    def test_clear_all_rankings(self, db_conn, test_user):
        """Test clearing all rankings for a user."""
        set_project_rank(db_conn, test_user, "Project A", 1)
        set_project_rank(db_conn, test_user, "Project B", 2)
        set_project_rank(db_conn, test_user, "Project C", 3)

        clear_all_rankings(db_conn, test_user)

        ranks = get_all_project_ranks(db_conn, test_user)
        assert len(ranks) == 0

    def test_bulk_set_rankings(self, db_conn, test_user):
        """Test bulk setting multiple rankings."""
        rankings = [
            ("Project A", 1),
            ("Project B", 2),
            ("Project C", 3),
        ]
        bulk_set_rankings(db_conn, test_user, rankings)

        all_ranks = get_all_project_ranks(db_conn, test_user)
        assert len(all_ranks) == 3
        assert all_ranks[0] == ("Project A", 1)
        assert all_ranks[1] == ("Project B", 2)
        assert all_ranks[2] == ("Project C", 3)

    def test_update_existing_rank(self, db_conn, test_user):
        """Test updating an existing rank."""
        set_project_rank(db_conn, test_user, "Project A", 1)
        set_project_rank(db_conn, test_user, "Project A", 5)

        rank = get_project_rank(db_conn, test_user, "Project A")
        assert rank == 5

class TestRankingLogic:
    """Test the integration with project ranking logic."""

    def test_collect_project_data_with_manual_ranks(self, db_conn, test_user, test_projects):
        """Test that collect_project_data respects manual rankings."""
        # Set manual rank for Project Gamma (lowest auto-score)
        set_project_rank(db_conn, test_user, "Project Gamma", 1)

        ranked_projects = collect_project_data(db_conn, test_user, respect_manual_ranking=True)

        # Project Gamma should be first despite low auto-score
        assert ranked_projects[0][0] == "Project Gamma"

    def test_collect_project_data_without_manual_ranks(self, db_conn, test_user, test_projects):
        """Test that collect_project_data can ignore manual rankings."""
        set_project_rank(db_conn, test_user, "Project Gamma", 1)

        ranked_projects = collect_project_data(db_conn, test_user, respect_manual_ranking=False)

        # Project Gamma should NOT be first when ignoring manual ranks
        assert ranked_projects[0][0] != "Project Gamma"

    def test_mixed_manual_and_auto_ranking(self, db_conn, test_user, test_projects):
        """Test mixing manual and automatic rankings."""
        # Manually rank only some projects
        set_project_rank(db_conn, test_user, "Project Beta", 1)
        set_project_rank(db_conn, test_user, "Project Gamma", 2)

        ranked_projects = collect_project_data(db_conn, test_user, respect_manual_ranking=True)

        # First two should be manually ranked
        assert ranked_projects[0][0] == "Project Beta"
        assert ranked_projects[1][0] == "Project Gamma"

        # Remaining should be auto-sorted
        # Project Delta (0.91) should be before Project Alpha (0.85)
        remaining_projects = [name for name, score in ranked_projects[2:]]
        assert "Project Delta" in remaining_projects
        assert "Project Alpha" in remaining_projects

    def test_all_projects_manually_ranked(self, db_conn, test_user, test_projects):
        """Test when all projects have manual ranks."""
        set_project_rank(db_conn, test_user, "Project Delta", 1)
        set_project_rank(db_conn, test_user, "Project Alpha", 2)
        set_project_rank(db_conn, test_user, "Project Beta", 3)
        set_project_rank(db_conn, test_user, "Project Gamma", 4)

        ranked_projects = collect_project_data(db_conn, test_user, respect_manual_ranking=True)

        assert ranked_projects[0][0] == "Project Delta"
        assert ranked_projects[1][0] == "Project Alpha"
        assert ranked_projects[2][0] == "Project Beta"
        assert ranked_projects[3][0] == "Project Gamma"