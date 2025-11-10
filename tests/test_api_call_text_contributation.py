import pytest
from unittest.mock import MagicMock
from src.google_drive.api_calls import analyze_google_doc

# Helper
def mock_service():
    service = MagicMock()
    # Revisions metadata
    service.revisions().list().execute.return_value = {
        "revisions": [
            {"id": "rev1", "lastModifyingUser": {"emailAddress": "user@example.com"}, "modifiedTime": "2025-01-01T10:00:00Z"},
            {"id": "rev2", "lastModifyingUser": {"emailAddress": "user@example.com"}, "modifiedTime": "2025-01-02T11:00:00Z"},
            {"id": "rev3", "lastModifyingUser": {"emailAddress": "other@example.com"}, "modifiedTime": "2025-01-03T12:00:00Z"}
        ]
    }
    # Google Doc content
    service.documents().get().execute.return_value = {
        "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Hello world"}}]}},
                             {"paragraph": {"elements": [{"textRun": {"content": "Another paragraph"}}]}}]}
    }
    return service

# Tests
def test_user_revisions():
    result = analyze_google_doc(mock_service(), "file-id", "user@example.com")
    assert result["status"] == "analyzed"
    assert result["revision_count"] == 2
    assert result["total_revision_count"] == 3

def test_no_user_revisions():
    result = analyze_google_doc(mock_service(), "file-id", "nonexistent@example.com")
    assert result["revision_count"] == 0
    assert result["revisions"] == []

def test_api_failure(monkeypatch):
    service = mock_service()
    from googleapiclient.errors import HttpError
    mock_resp = type("Resp", (), {"status": 500, "reason": "Internal Server Error"})()
    service.revisions().list.side_effect = HttpError(resp=mock_resp, content=b"error")
    result = analyze_google_doc(service, "file-id", "user@example.com")
    assert result["status"] == "failed"
