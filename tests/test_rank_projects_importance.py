"""
Tests for rank_project_importance.py functions.
"""
import pytest
import json
from src.db import connect, init_schema, get_or_create_user, save_project_summary
from src.insights.rank_projects.rank_project_importance import collect_project_data, combine_scores


def _summary_dict(**kwargs):
    """Helper to create ProjectSummary dict."""
    return {
        "project_name": kwargs.get("project_name", "Test"),
        "project_type": kwargs.get("project_type", "code"),
        "project_mode": kwargs.get("project_mode", "individual"),
        "languages": kwargs.get("languages", []),
        "frameworks": kwargs.get("frameworks", []),
        "metrics": kwargs.get("metrics", {}),
        "contributions": kwargs.get("contributions", {}),
        "created_at": "2024-01-01T00:00:00+00:00"
    }


@pytest.mark.parametrize("results,expected", [
    ([(0.8, True, 0.3), (0.6, True, 0.2), (0.4, True, 0.1)], (0.8 * 0.3 + 0.6 * 0.2 + 0.4 * 0.1) / 0.6),
    ([(0.8, True, 0.3), (0.6, False, 0.2), (0.4, True, 0.1)], (0.8 * 0.3 + 0.4 * 0.1) / 0.4),
    ([(0.8, False, 0.3), (0.6, False, 0.2)], 0.0),
    ([], 0.0),
])
def test_combine_scores(results, expected):
    """Test combine_scores with various inputs."""
    score = combine_scores(results)
    assert abs(score - expected) < 0.001


@pytest.fixture
def setup_user():
    """Create test user."""
    conn = connect()
    init_schema(conn)
    user_id = get_or_create_user(conn, "testuser")
    yield conn, user_id
    conn.close()


def test_collect_project_data_single(setup_user):
    """Test collecting data for single project."""
    conn, user_id = setup_user
    summary = _summary_dict(
        project_name="TestProject",
        metrics={"skills_detailed": [{"score": 0.8}], "activity_type": {"writing": 1}}
    )
    save_project_summary(conn, user_id, "TestProject", json.dumps(summary))
    results = collect_project_data(conn, user_id)
    assert len(results) == 1
    assert results[0][0] == "TestProject"
    assert 0.0 <= results[0][1] <= 1.0


def test_collect_project_data_multiple_sorted(setup_user):
    """Test multiple projects are sorted by score."""
    conn, user_id = setup_user
    high = _summary_dict(project_name="High", metrics={"skills_detailed": [{"score": 0.9}], "activity_type": {"writing": 1}, "complexity": {"summary": {"total_files": 30, "total_lines": 5000, "total_functions": 50, "avg_complexity": 5, "maintainability_index": 90}}})
    low = _summary_dict(project_name="Low", metrics={"skills_detailed": [{"score": 0.3}], "activity_type": {"writing": 1}})
    save_project_summary(conn, user_id, "High", json.dumps(high))
    save_project_summary(conn, user_id, "Low", json.dumps(low))
    results = collect_project_data(conn, user_id)
    assert len(results) == 2
    assert results[0][1] >= results[1][1]


def test_collect_project_data_no_projects(setup_user):
    """Test when user has no projects."""
    conn, user_id = setup_user
    results = collect_project_data(conn, user_id)
    assert results == []


def test_collect_project_data_text_project(setup_user):
    """Test text project collection."""
    conn, user_id = setup_user
    summary = _summary_dict(
        project_name="TextProj",
        project_type="text",
        metrics={"skills_detailed": [{"score": 0.7}], "activity_type": {"writing": 1}, "text": {"llm": {"overall_score": 0.85}}}
    )
    save_project_summary(conn, user_id, "TextProj", json.dumps(summary))
    results = collect_project_data(conn, user_id)
    assert len(results) == 1
    assert results[0][0] == "TextProj"
