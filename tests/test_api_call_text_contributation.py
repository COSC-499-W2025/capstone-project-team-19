import pytest
from unittest.mock import MagicMock
from src.google_drive.api_calls import analyze_google_doc

# Helper
def mock_services():
    drive_service = MagicMock()
    docs_service = MagicMock()
    # Revisions metadata
    drive_service.revisions().list().execute.return_value = {
        "revisions": [
            {"id": "rev1", "lastModifyingUser": {"emailAddress": "user@example.com"}, "modifiedTime": "2025-01-01T10:00:00Z"},
            {"id": "rev2", "lastModifyingUser": {"emailAddress": "user@example.com"}, "modifiedTime": "2025-01-02T11:00:00Z"},
            {"id": "rev3", "lastModifyingUser": {"emailAddress": "other@example.com"}, "modifiedTime": "2025-01-03T12:00:00Z"}
        ]
    }
    # Google Doc content
    docs_service.documents().get().execute.return_value = {
        "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Hello world"}}]}},
                             {"paragraph": {"elements": [{"textRun": {"content": "Another paragraph"}}]}}]}
    }
    return drive_service, docs_service

# Tests
def test_user_revisions():
    drive_service, docs_service = mock_services()
    result = analyze_google_doc(drive_service, docs_service, "file-id", "user@example.com", creds=None)
    assert result["status"] == "analyzed"
    assert result["revision_count"] == 2
    assert result["total_revision_count"] == 3

def test_no_user_revisions():
    drive_service, docs_service = mock_services()
    result = analyze_google_doc(drive_service, docs_service, "file-id", "nonexistent@example.com", creds=None)
    assert result["revision_count"] == 0
    assert result["revisions"] == []

def test_api_failure(monkeypatch):
    drive_service, docs_service = mock_services()
    from googleapiclient.errors import HttpError
    mock_resp = type("Resp", (), {"status": 500, "reason": "Internal Server Error"})()
    drive_service.revisions().list.side_effect = HttpError(resp=mock_resp, content=b"error")
    result = analyze_google_doc(drive_service, docs_service, "file-id", "user@example.com", creds=None)
    assert result["status"] == "failed"
