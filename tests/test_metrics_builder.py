# test_metrics_builder.py

import pytest
from unittest.mock import patch, MagicMock

from src.summary.metrics_builder import (
    build_all_project_metrics,
    build_code_metrics,
    build_text_metrics,
)
from src.summary.metrics_model import CodeProjectMetrics, TextProjectMetrics


# Helpers

def make_gh_row():
    return (
        50, 10, "2024-01-01", "2024-02-01",
        3, 1, 2, 2, 120, 40, 75.0
    )

def assert_gh_fields(obj, gh):
    (
        commits, days, first, last,
        opened, closed, prs_opened, prs_merged,
        adds, dels, percent
    ) = gh

    assert obj.github_total_commits == commits
    assert obj.github_commit_days == days
    assert obj.github_first_commit == first
    assert obj.github_last_commit == last
    assert obj.github_issues_opened == opened
    assert obj.github_issues_closed == closed
    assert obj.github_prs_opened == prs_opened
    assert obj.github_prs_merged == prs_merged
    assert obj.github_additions == adds
    assert obj.github_deletions == dels
    assert obj.github_contribution_percent == percent


# Tests

@patch("src.summary.metrics_builder.fetch_all_project_metadata")
@patch("src.summary.metrics_builder.fetch_github_metrics_row")
def test_build_all_project_metrics(mock_gh, mock_meta):
    mock_meta.return_value = [
        ("ProjA", "individual", "code"),
        ("Text1", "collaborative", "text")
    ]
    mock_gh.return_value = make_gh_row()

    result = build_all_project_metrics(MagicMock(), user_id=1)

    assert isinstance(result[0], CodeProjectMetrics)
    assert isinstance(result[1], TextProjectMetrics)
    assert result[0].classification == "individual"
    assert result[1].classification == "collaborative"


@patch("src.summary.metrics_builder.fetch_github_metrics_row")
def test_build_code_metrics_populates(mock_gh):
    gh = make_gh_row()
    mock_gh.return_value = gh

    obj = build_code_metrics(MagicMock(), 1, "A", "collaborative")
    assert_gh_fields(obj, gh)
    assert obj.is_collaborative is True


@patch("src.summary.metrics_builder.fetch_github_metrics_row")
def test_build_code_metrics_no_github(mock_gh):
    mock_gh.return_value = None
    obj = build_code_metrics(MagicMock(), 1, "A", "individual")

    # all None
    assert obj.github_total_commits is None
    assert obj.is_collaborative is False


def test_build_text_metrics_defaults():
    obj = build_text_metrics(MagicMock(), 1, "T", "collaborative")

    assert isinstance(obj, TextProjectMetrics)
    assert obj.is_collaborative is True
    assert obj.summary is None
    assert obj.skills is None

@patch("src.summary.metrics_builder.fetch_all_project_metadata")
def test_build_all_project_metrics_empty(mock_meta):
    mock_meta.return_value = []
    result = build_all_project_metrics(MagicMock(), user_id=1)
    assert result == []

@patch("src.summary.metrics_builder.fetch_all_project_metadata")
def test_unexpected_project_type_defaults_to_text(mock_meta):
    mock_meta.return_value = [
        ("WeirdProj", "individual", "???")
    ]
    result = build_all_project_metrics(MagicMock(), user_id=1)
    assert isinstance(result[0], TextProjectMetrics)

@patch("src.summary.metrics_builder.fetch_github_metrics_row")
def test_partial_github_row_allowed(mock_gh):
    row = (
        50, None, None, None,
        1, None, 2, None,
        10, 5, None
    )
    mock_gh.return_value = row
    obj = build_code_metrics(MagicMock(), 1, "A", "individual")
    assert obj.github_total_commits == 50
    assert obj.github_commit_days is None

@patch("src.summary.metrics_builder.fetch_all_project_metadata")
@patch("src.summary.metrics_builder.fetch_github_metrics_row")
def test_multiple_projects_mixed(mock_gh, mock_meta):
    mock_meta.return_value = [
        ("A", "individual", "code"),
        ("B", "collaborative", "code"),
        ("C", "individual", "text"),
    ]
    mock_gh.side_effect = [
        make_gh_row(),
        None,
        None,
    ]

    result = build_all_project_metrics(MagicMock(), 1)

    assert isinstance(result[0], CodeProjectMetrics)
    assert result[0].github_total_commits == 50

    assert isinstance(result[1], CodeProjectMetrics)
    assert result[1].github_total_commits is None  # no GitHub data

    assert isinstance(result[2], TextProjectMetrics)
