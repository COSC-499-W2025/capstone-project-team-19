import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics import build_drive_collaboration_metrics,run_drive_collaboration_analysis
from src.analysis.text_collaborative.drive_collaboration.models import RawUserTextCollabMetrics,RawTeamTextCollabMetrics


# HELPERS & FIXTURES
@pytest.fixture
def mock_drive_service():
    return Mock()


def make_comment_result(user_comments=0, user_replies=0, user_questions=0, 
                       team_comments=0, team_replies=0, team_questions=0):
    """Helper to create a comment fetch result."""
    user_comment_texts = [f"Comment {i+1}" for i in range(user_comments)]
    user_reply_texts = [f"Reply {i+1}" for i in range(user_replies)]
    user_question_texts = [f"Question {i+1}?" for i in range(user_questions)]
    
    team_comment_texts = user_comment_texts + [f"Other comment {i+1}" for i in range(team_comments - user_comments)]
    team_reply_texts = user_reply_texts + [f"Other reply {i+1}" for i in range(team_replies - user_replies)]
    team_question_texts = user_question_texts + [f"Other question {i+1}?" for i in range(team_questions - user_questions)]
    
    return {
        "status": "success",
        "user": {
            "comments": user_comment_texts,
            "replies": user_reply_texts,
            "questions": user_question_texts,
            "comment_timestamps": [datetime(2025, 1, i+1) for i in range(user_comments)],
            "reply_timestamps": [datetime(2025, 1, i+10) for i in range(user_replies)]
        },
        "team": {
            "comments": team_comment_texts,
            "replies": team_reply_texts,
            "questions": team_question_texts
        }
    }


# TESTS

@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_single_file(mock_fetch, mock_drive_service):
    """Test building metrics from a single file."""
    mock_fetch.return_value = make_comment_result(user_comments=2, user_replies=1, user_questions=1,
                                                  team_comments=3, team_replies=2, team_questions=1)
    
    user, team = build_drive_collaboration_metrics(mock_drive_service, ["file1"], "user@example.com", "Test User")
    assert isinstance(user, RawUserTextCollabMetrics)
    assert user.comments_posted == 2
    assert user.replies_posted == 1
    assert user.questions_asked == 1
    assert len(user.files_commented_on) == 1
    assert isinstance(team, RawTeamTextCollabMetrics)
    assert team.total_comments == 3
    assert team.total_replies == 2


@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_multiple_files(mock_fetch, mock_drive_service):
    """Test aggregation across multiple files."""
    def side_effect(service, file_id, email, name):
        if file_id == "file1":
            return make_comment_result(user_comments=2, team_comments=3)
        return make_comment_result(user_comments=1, team_comments=1)
    mock_fetch.side_effect = side_effect
    user, team = build_drive_collaboration_metrics(mock_drive_service, ["file1", "file2"], "user@example.com", "Test User")
    assert user.comments_posted == 3  # 2 + 1
    assert len(user.files_commented_on) == 2
    assert team.total_comments == 4  # 3 + 1
    assert team.total_files == 2


@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_empty_files(mock_fetch, mock_drive_service):
    """Test that no comments result in zero metrics."""
    user, team = build_drive_collaboration_metrics(mock_drive_service, [], "user@example.com", "Test User")
    assert user.comments_posted == 0
    assert team.total_comments == 0
    assert team.total_files == 0


@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_failed_api_call(mock_fetch, mock_drive_service):
    """Test that failed API calls are skipped."""
    def side_effect(service, file_id, email, name):
        if file_id == "file1":
            return {"status": "failed", "error": "API error"}
        return make_comment_result(user_comments=1, team_comments=1)
    mock_fetch.side_effect = side_effect
    user, team = build_drive_collaboration_metrics(mock_drive_service, ["file1", "file2"], "user@example.com", "Test User")
    assert user.comments_posted == 1  # Only from file2
    assert team.total_comments == 1


@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_files_commented_on(mock_fetch, mock_drive_service):
    """Test that files_commented_on is tracked correctly."""
    def side_effect(service, file_id, email, name):
        if file_id == "file1":
            return make_comment_result(user_comments=1, team_comments=1)
        return make_comment_result(user_comments=0, team_comments=1)  # User didn't comment
    mock_fetch.side_effect = side_effect
    user, team = build_drive_collaboration_metrics(mock_drive_service, ["file1", "file2"], "user@example.com", "Test User")
    assert len(user.files_commented_on) == 1
    assert "file1" in user.files_commented_on
    assert "file2" not in user.files_commented_on

@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_build_metrics_timestamps_filtered(mock_fetch, mock_drive_service):
    """Test that None timestamps are filtered out."""
    result = make_comment_result(user_comments=2, team_comments=2)
    result["user"]["comment_timestamps"] = [None, datetime(2025, 1, 1)]  # One None
    mock_fetch.return_value = result
    user, team = build_drive_collaboration_metrics(mock_drive_service, ["file1"], "user@example.com", "Test User")
    assert len(user.comment_timestamps) == 1  # None filtered out
    assert user.comment_timestamps[0] == datetime(2025, 1, 1)