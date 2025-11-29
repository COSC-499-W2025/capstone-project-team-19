"""
Tests for extract_scores.py functions.
"""
import pytest
from src.models.project_summary import ProjectSummary
from src.insights.rank_projects.extract_scores import (
    _extract_base_scores, _extract_text_scores, _extract_code_scores
)


def _ps(**kwargs):
    """Helper to create ProjectSummary."""
    return ProjectSummary(
        project_name=kwargs.get("project_name", "Test"),
        project_type=kwargs.get("project_type", "code"),
        project_mode=kwargs.get("project_mode", "individual"),
        languages=kwargs.get("languages", []),
        frameworks=kwargs.get("frameworks", []),
        metrics=kwargs.get("metrics", {}),
        contributions=kwargs.get("contributions", {}),
    )


def test_extract_base_scores_happy_path():
    """Test _extract_base_scores with all metrics."""
    ps = _ps(metrics={
        "skills_detailed": [{"score": 0.8}],
        "activity_type": {"writing": 1}
    })
    results = _extract_base_scores(ps, is_collab=False)
    assert len(results) == 3
    assert all(isinstance(r[0], float) and isinstance(r[1], bool) and isinstance(r[2], float) for r in results)
    assert results[0][2] == 0.30 and results[1][2] == 0.20 and results[2][2] == 0.10


def test_extract_base_scores_missing_data():
    """Test _extract_base_scores with missing metrics."""
    ps = _ps()
    results = _extract_base_scores(ps, is_collab=False)
    assert len(results) == 3
    # skill_strength and activity_diversity unavailable, but contribution_strength is available for individual
    assert results[0][1] is False  # skill_strength
    assert results[1][1] is True   # contribution_strength (individual always 1.0)
    assert results[2][1] is False  # activity_diversity


def test_extract_text_scores_happy_path():
    """Test _extract_text_scores with LLM score."""
    ps = _ps(project_type="text", metrics={"text": {"llm": {"overall_score": 0.85}}})
    results = _extract_text_scores(ps)
    assert len(results) == 1
    assert results[0][1] is True
    assert results[0][0] == 0.85
    assert results[0][2] == 0.40


def test_extract_text_scores_missing():
    """Test _extract_text_scores with missing metrics."""
    ps = _ps(project_type="text")
    results = _extract_text_scores(ps)
    assert len(results) == 1
    assert results[0][1] is False


def test_extract_code_scores_happy_path():
    """Test _extract_code_scores with all metrics."""
    ps = _ps(project_type="code", languages=["Python"], frameworks=["Django"], metrics={
        "complexity": {"summary": {"total_files": 20, "total_lines": 3000, "total_functions": 30, "avg_complexity": 5, "maintainability_index": 80}},
        "git": {"commit_stats": {"total_commits": 40, "active_days": 15, "commit_span_days": 30}},
        "github": {"prs_opened": 5, "issues_opened": 3, "contribution_percent": 100, "total_additions": 2000, "total_deletions": 500}
    })
    results = _extract_code_scores(ps, is_collab=False)
    assert len(results) == 4
    assert all(isinstance(r[0], float) and isinstance(r[1], bool) for r in results)


def test_extract_code_scores_collaborative():
    """Test _extract_code_scores for collaborative project."""
    ps = _ps(project_type="code", project_mode="collaborative", metrics={
        "complexity": {"summary": {"total_files": 15, "total_lines": 2000, "total_functions": 20, "avg_complexity": 4}},
        "github": {"contribution_percent": 60}
    })
    results = _extract_code_scores(ps, is_collab=True)
    assert len(results) == 4
    assert all(isinstance(r[0], float) and isinstance(r[1], bool) for r in results)
