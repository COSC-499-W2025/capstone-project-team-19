import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics import run_drive_collaboration_analysis

# HELPERS & FIXTURES
@pytest.fixture
def mock_drive_service():
    return Mock()

def make_comment_result(user_comments=2, user_replies=1, user_questions=1):
    """Helper to create comment fetch result."""
    return {
        "status": "success",
        "user": {
            "comments": [f"Comment {i+1}" for i in range(user_comments)],
            "replies": [f"Reply {i+1}" for i in range(user_replies)],
            "questions": [f"Question {i+1}?" for i in range(user_questions)],
            "comment_timestamps": [datetime(2025, 1, i+1) for i in range(user_comments)],
            "reply_timestamps": [datetime(2025, 1, i+10) for i in range(user_replies)]
        },
        "team": {
            "comments": [f"Comment {i+1}" for i in range(user_comments + 1)],
            "replies": [f"Reply {i+1}" for i in range(user_replies + 1)],
            "questions": [f"Question {i+1}?" for i in range(user_questions)]
        }
    }


# TESTS
@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_run_analysis_full_pipeline(mock_fetch, mock_drive_service):
    mock_fetch.return_value = make_comment_result()
    
    profile = run_drive_collaboration_analysis(mock_drive_service, ["file1"], "user@example.com", "Test User")
    
    assert "normalized" in profile
    assert "skills" in profile
    assert "skill_levels" in profile
    
    assert "written_communication" in profile["skills"]
    assert "participation" in profile["skills"]
    assert "communication_leadership" in profile["skills"]
    
    valid_levels = {"Beginner", "Intermediate", "Advanced"}
    assert profile["skill_levels"]["written_communication"] in valid_levels
    assert profile["skill_levels"]["participation"] in valid_levels
    assert profile["skill_levels"]["communication_leadership"] in valid_levels


@patch("src.analysis.text_collaborative.drive_collaboration.build_drive_collab_metrics.fetch_drive_comments")
def test_run_analysis_empty_comments(mock_fetch, mock_drive_service):
    mock_fetch.return_value = make_comment_result(user_comments=0, user_replies=0, user_questions=0)
    
    profile = run_drive_collaboration_analysis(mock_drive_service, ["file1"], "user@example.com", "Test User")
    assert "skills" in profile
    assert "skill_levels" in profile
    assert profile["skills"]["written_communication"]["score"] == 0
    assert profile["skills"]["participation"]["activity_score"] == 0