"""
Tests for project ranking scoring functions.
"""
import pytest
import math
from src.models.project_summary import ProjectSummary
from src.insights.rank_projects.code_scoring_functions import (
    code_complexity, git_activity, github_collaboration, tech_stack
)
from src.insights.rank_projects.text_scoring_functions import writing_quality
from src.insights.rank_projects.shared_scoring_functions import (
    skill_strength, contribution_strength, activity_diversity
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


@pytest.mark.parametrize("func,metrics,expected_avail", [
    (code_complexity, {"complexity": {"summary": {"total_files": 30, "total_lines": 5000, "total_functions": 50, "avg_complexity": 5, "maintainability_index": 80}}}, True),
    (code_complexity, {}, False),
    (code_complexity, {"complexity": "not dict"}, False),
    (git_activity, {"git": {"commit_stats": {"total_commits": 50, "active_days": 20, "commit_span_days": 40}}}, True),
    (git_activity, {}, False),
    (github_collaboration, {"github": {"prs_opened": 10, "issues_opened": 10, "contribution_percent": 50, "total_additions": 5000, "total_deletions": 2000}}, True),
    (github_collaboration, {}, False),
    (tech_stack, {}, True),  # Always available, just returns 0.0
    (writing_quality, {"text": {"llm": {"overall_score": 0.85}}}, True),
    (writing_quality, {"text": {"non_llm": {"reading_level_avg": 12}}}, True),
    (writing_quality, {}, False),
    (skill_strength, {"skills_detailed": [{"score": 0.8}, {"score": 0.6}]}, True),
    (skill_strength, {}, False),
])
def test_scoring_functions(func, metrics, expected_avail):
    """Test scoring functions with various inputs."""
    ps = _ps(metrics=metrics)
    score, available = func(ps)
    assert available == expected_avail
    assert 0.0 <= score <= 1.0


def test_tech_stack_with_languages():
    """Test tech_stack with languages and frameworks."""
    ps = _ps(languages=["Python", "JavaScript"], frameworks=["React"])
    score, available = tech_stack(ps)
    assert available is True
    assert score > 0.0


@pytest.mark.parametrize("is_collab,metrics,contributions,expected_avail", [
    (False, {}, {}, True),
    (True, {}, {"text_collab": {"percent_of_document": 60}}, True),
    (True, {"github": {"contribution_percent": 80}}, {}, True),
    (True, {}, {}, False),
])
def test_contribution_strength(is_collab, metrics, contributions, expected_avail):
    """Test contribution_strength for individual vs collaborative."""
    ps = _ps(metrics=metrics, contributions=contributions)
    score, available = contribution_strength(ps, is_collab)
    assert available == expected_avail
    if not is_collab:
        assert score == 1.0


@pytest.mark.parametrize("is_collab,metrics,contributions,expected_avail", [
    (False, {"activity_type": {"writing": 1, "editing": 1}}, {}, True),
    (True, {}, {"activity_type": {"writing": 1}}, True),
    (True, {"activity_type": {"writing": 1}}, {}, True),  # Fallback to metrics
    (False, {}, {}, False),
])
def test_activity_diversity(is_collab, metrics, contributions, expected_avail):
    """Test activity_diversity for individual vs collaborative."""
    ps = _ps(metrics=metrics, contributions=contributions)
    score, available = activity_diversity(ps, is_collab)
    assert available == expected_avail
    if expected_avail:
        assert 0.0 <= score <= 1.0


def test_writing_quality_capped():
    """Test writing_quality score capping."""
    ps = _ps(metrics={"text": {"llm": {"overall_score": 1.5}}})
    score, available = writing_quality(ps)
    assert available is True
    assert score == 1.0


def test_code_complexity_capped():
    """Test code_complexity value capping."""
    ps = _ps(metrics={"complexity": {"summary": {
        "total_files": 100, "total_lines": 20000, "total_functions": 200,
        "avg_complexity": 20, "maintainability_index": 100
    }}})
    score, available = code_complexity(ps)
    assert available is True
    assert score <= 1.0
