import pytest
from unittest.mock import patch
from datetime import datetime

from src.analysis.code_collaborative.github_collaboration.build_collab_metrics import build_collaboration_metrics, run_collaboration_analysis
from src.analysis.code_collaborative.github_collaboration.models import RawUserCollabMetrics, RawTeamCollabMetrics

# Fake GitHub API return for mocking fetch_github_metrics()
def fake_github_metrics():
    return {
        "repository": "owner/repo",
        "username": "timmi",

        # {date: commits}
        "commits": {
            "2024-01-01": 3,
            "2024-01-02": 2,
        },

        "issues": {
            "total_opened": 5,
            "total_closed": 3,
            "user_issues": [],
            "user_issue_comments": [{"c": 1}, {"c": 2}],
        },

        "pull_requests": {
            "total_opened": 4,
            "total_merged": 3,
            "user_prs": [
                {"created_at": "2024-01-02T10:00:00"},
                {"created_at": "2024-01-03T12:00:00"},
            ],
        },

        "contributions": {
            "user": {
                "additions": 150,
                "deletions": 50,
            },
            "team": {
                "total_commits": 20,
                "total_additions": 500,
                "total_deletions": 200,
            },
        },

        "commit_timestamps": [
            datetime(2024, 1, 1, 10, 0),
            datetime(2024, 1, 2, 10, 0),
        ],

        # GraphQL PR data
        "graphql_prs": {
            "prs_opened": 2,
            "prs_reviewed": 1,
            "review_comments": ["Looks good to me", "Consider renaming variable"],
            "review_timestamps": ["2024-01-02T10:00:00Z"],
            "pr_timestamps": ["2024-01-02T10:00:00Z", "2024-01-03T12:00:00Z"],
            "user_pr_discussion_comments": 0,
            "team_pr_discussion_comments": 0,
            "team_total_prs": 4,
            "team_total_reviews": 1,
            "user_prs": [
                {"created_at": "2024-01-02T10:00:00"},
                {"created_at": "2024-01-03T12:00:00"},
            ],
            "reviews": {
                1: {
                    "reviews": [
                        {"submitted_at": "2024-01-02T10:00:00"}
                    ],
                    "review_comments": [
                        {"body": "Looks good to me"},
                        {"body": "Consider renaming variable"},
                    ],
                },
            }
        },

        # Review structure: mapping PR number to review data
        "reviews": {
            1: {
                "reviews": [
                    {"submitted_at": "2024-01-02T10:00:00"}
                ],
                "review_comments": [
                    {"body": "Looks good to me"},
                    {"body": "Consider renaming variable"},
                ],
            },
        },
    }


# Test build_collaboration_metrics
@patch("src.analysis.code_collaborative.github_collaboration.build_collab_metrics.fetch_github_metrics")
def test_build_collaboration_metrics_basic(mock_fetch):
    mock_fetch.return_value = fake_github_metrics()

    user, team = build_collaboration_metrics("token", "owner", "repo", "timmi")

    # Validate user metrics
    assert isinstance(user, RawUserCollabMetrics)
    # commits = 3 + 2
    assert user.commits == 5
    # PRs opened = 2 (from user_prs list)
    assert user.prs_opened == 2
    # reviewers = number of review events
    assert user.prs_reviewed == 1  # one submitted review
    assert user.issues_opened == 0  # empty user_issues list
    assert user.issue_comments == 2
    # timestamps
    assert len(user.commit_timestamps) == 2
    assert len(user.pr_timestamps) == 2
    assert len(user.review_timestamps) == 1
    # review comments collected
    assert len(user.review_comments) == 2
    assert "Looks good to me" in user.review_comments
    assert user.additions == 150
    assert user.deletions == 50

    # Validate TEAM metrics
    assert isinstance(team, RawTeamCollabMetrics)
    assert team.total_commits == 20
    assert team.total_prs == 4
    assert team.total_reviews == 1
    assert team.total_issues == 5
    assert team.total_issue_comments == 0
    assert team.total_pr_discussion_comments == 0
    assert team.total_review_comments == 2
    assert team.total_additions == 500
    assert team.total_deletions == 200


# Test run_collaboration_analysis (integration with compute_collaboration_profile)
@patch("src.analysis.code_collaborative.github_collaboration.build_collab_metrics.fetch_github_metrics")
def test_run_collaboration_analysis(mock_fetch):
    mock_fetch.return_value = fake_github_metrics()

    profile = run_collaboration_analysis("token", "owner", "repo", "timmi")

    assert "normalized" in profile
    assert "skills" in profile

    # validate presence of expected skill categories
    assert "review_quality" in profile["skills"]
    assert "participation" in profile["skills"]
    assert "consistency" in profile["skills"]
    assert "leadership" in profile["skills"]

    # review_quality_score produced
    assert profile["skills"]["review_quality"]["total_comments"] == 2
