import pytest
from unittest.mock import Mock
from datetime import datetime
from googleapiclient.errors import HttpError
from src.integrations.google_drive.api_calls import fetch_drive_comments

# HELPERS & FIXTURES
@pytest.fixture
def mock_drive_service():
    """Mock Drive service with configurable comment responses."""
    service = Mock()
    service.comments.return_value.list.return_value.execute.return_value = {"comments": []}
    return service


def make_comment(comment_id, content, author_name, author_email="", replies=None, created_time="2025-01-01T10:00:00Z"):
    """Helper to create a comment dict."""
    return {
        "id": comment_id,
        "content": content,
        "author": {"displayName": author_name, "emailAddress": author_email},
        "createdTime": created_time,
        "replies": replies or []
    }

def make_reply(reply_id, content, author_name, author_email="", created_time="2025-01-01T11:00:00Z"):
    """Helper to create a reply dict."""
    return {
        "id": reply_id,
        "content": content,
        "author": {"displayName": author_name, "emailAddress": author_email},
        "createdTime": created_time
    }

def setup_comments(mock_service, comments_list):
    """Setup mock service to return specific comments."""
    mock_service.comments.return_value.list.return_value.execute.return_value = {
        "comments": comments_list
    }

# TESTS
def test_fetch_drive_comments_empty(mock_drive_service):
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert result["status"] == "success"
    assert len(result["user"]["comments"]) == 0
    assert len(result["team"]["comments"]) == 0


def test_fetch_drive_comments_match_by_displayname_exact(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "User comment", "Test User"),
        make_comment("c2", "Other comment", "Other User")
    ])   
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["comments"]) == 1
    assert result["user"]["comments"][0] == "User comment"
    assert len(result["team"]["comments"]) == 2


def test_fetch_drive_comments_match_by_displayname_case_insensitive(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "Comment", "test user")  
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["comments"]) == 1


def test_fetch_drive_comments_match_by_email(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "Email match", "Different Name", "user@example.com")
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["comments"]) == 1
    assert result["user"]["comments"][0] == "Email match"


def test_fetch_drive_comments_questions_detection(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "What is this?", "Test User"),
        make_comment("c2", "This looks good", "Test User")
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["questions"]) == 1
    assert result["user"]["questions"][0] == "What is this?"
    assert len(result["team"]["questions"]) == 1

def test_fetch_drive_comments_with_replies(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "Original", "Other User", replies=[
            make_reply("r1", "Reply from user", "Test User")
        ])
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["comments"]) == 0
    assert len(result["user"]["replies"]) == 1
    assert result["user"]["replies"][0] == "Reply from user"


def test_fetch_drive_comments_timestamps(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "Comment", "Test User", created_time="2025-01-01T10:00:00Z")
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert len(result["user"]["comment_timestamps"]) == 1
    assert isinstance(result["user"]["comment_timestamps"][0], datetime)

def test_fetch_drive_comments_no_displayname(mock_drive_service):
    setup_comments(mock_drive_service, [
        make_comment("c1", "Comment", "Test User")
    ])
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", None)
    assert len(result["user"]["comments"]) == 0  # Can't match without displayName

def test_fetch_drive_comments_http_error(mock_drive_service):
    mock_drive_service.comments.return_value.list.return_value.execute.side_effect = HttpError(
        resp=Mock(status=404), content=b'{"error": "Not found"}'
    )
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert result["status"] == "failed"
    assert "error" in result

def test_fetch_drive_comments_general_exception(mock_drive_service):
    mock_drive_service.comments.return_value.list.return_value.execute.side_effect = Exception("Network error")
    result = fetch_drive_comments(mock_drive_service, "file123", "user@example.com", "Test User")
    assert result["status"] == "failed"