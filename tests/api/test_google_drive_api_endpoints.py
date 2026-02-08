import json
from unittest.mock import patch
from .conftest import client, auth_headers, seed_conn

def _create_test_upload(seed_conn, user_id: int) -> int:
    cursor = seed_conn.execute(
        "INSERT INTO uploads (user_id, zip_name, zip_path, status, state_json) VALUES (?, ?, ?, ?, ?)",
        (user_id, "test.zip", "/tmp/test.zip", "needs_classification", "{}")
    )
    seed_conn.commit()
    return cursor.lastrowid

def _setup_drive_oauth_state(seed_conn, upload_id: int, oauth_state: str, project_name: str = "TestProject"):
    seed_conn.execute(
        "UPDATE uploads SET state_json = ? WHERE upload_id = ?",
        (json.dumps({f"drive_{project_name}": {"oauth_state": oauth_state, "user_id": 1, "upload_id": upload_id, "project_name": project_name}}), upload_id)
    )
    seed_conn.commit()

# --- START ENDPOINT ---

def test_drive_start_requires_auth(client):
    res = client.post("/projects/upload/1/projects/TestProject/drive/start", json={"connect_now": True})
    assert res.status_code == 401

def test_drive_start_connect_now_false(client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/start", headers=auth_headers, json={"connect_now": False})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

@patch("src.services.google_drive_service.get_google_drive_token")
@patch("src.services.google_drive_service.generate_google_auth_url")
def test_drive_start_connect_now_true_generates_url(mock_auth_url, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    mock_auth_url.return_value = "https://accounts.google.com/o/oauth2/v2/auth?state=abc123"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] == "https://accounts.google.com/o/oauth2/v2/auth?state=abc123"
    mock_auth_url.assert_called_once()

@patch("src.services.google_drive_service.get_google_drive_token")
def test_drive_start_already_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "existing_token"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

def test_drive_start_upload_not_found(client, auth_headers):
    res = client.post("/projects/upload/999/projects/TestProject/drive/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 404

# --- CALLBACK ENDPOINT ---

@patch("src.services.google_drive_service.exchange_code_for_tokens")
@patch("src.services.google_drive_service.save_google_drive_tokens")
def test_drive_callback_success(mock_save_tokens, mock_exchange, client, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    _setup_drive_oauth_state(seed_conn, upload_id, "test_state_123")
    mock_exchange.return_value = {"access_token": "ya29.token123", "refresh_token": "1//refresh456", "expires_in": 3600}
    res = client.get("/auth/google/callback?code=abc123&state=test_state_123")
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_save_tokens.assert_called_once()
    call_positional = mock_save_tokens.call_args[0]
    call_kwargs = mock_save_tokens.call_args[1]
    # conn is [0], user_id=1 is [1]
    assert call_positional[1] == 1
    assert call_kwargs["access_token"] == "ya29.token123"

def test_drive_callback_missing_code(client):
    res = client.get("/auth/google/callback?state=test")
    assert res.status_code == 422

def test_drive_callback_invalid_state(client, seed_conn):
    _create_test_upload(seed_conn, 1)
    with patch("src.services.google_drive_service._find_upload_by_drive_oauth_state") as mock_find:
        mock_find.return_value = None
        res = client.get("/auth/google/callback?code=abc123&state=invalid")
        assert res.status_code == 400
        assert "Invalid OAuth state" in res.json()["detail"]

# --- FILES ENDPOINT ---

@patch("src.services.google_drive_service.get_google_drive_token")
@patch("src.services.google_drive_service._fetch_drive_files")
def test_drive_files_success(mock_fetch_files, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "ya29.token123"
    mock_fetch_files.return_value = [
        {"id": "file1", "name": "Report.docx", "mimeType": "application/vnd.google-apps.document"},
        {"id": "file2", "name": "Data.csv", "mimeType": "text/plain"},
    ]
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/drive/files", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]["files"]) == 2
    assert res.json()["data"]["files"][0]["id"] == "file1"
    assert res.json()["data"]["files"][0]["name"] == "Report.docx"
    assert res.json()["data"]["files"][0]["mime_type"] == "application/vnd.google-apps.document"

@patch("src.services.google_drive_service.get_google_drive_token")
def test_drive_files_not_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/drive/files", headers=auth_headers)
    assert res.status_code == 401
    assert "not connected" in res.json()["detail"].lower()

def test_drive_files_requires_auth(client, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/drive/files")
    assert res.status_code == 401

# --- LINK ENDPOINT ---

@patch("src.services.google_drive_service.get_google_drive_token")
@patch("src.services.google_drive_service.store_file_link")
def test_drive_link_success(mock_store_link, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "ya29.token123"
    body = {"links": [
        {"local_file_name": "report.docx", "drive_file_id": "file1", "drive_file_name": "Report.docx", "mime_type": "application/vnd.google-apps.document"},
        {"local_file_name": "data.csv", "drive_file_id": "file2", "drive_file_name": "Data.csv", "mime_type": "text/plain"},
    ]}
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/link", headers=auth_headers, json=body)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["files_linked"] == 2
    assert mock_store_link.call_count == 2

@patch("src.services.google_drive_service.get_google_drive_token")
def test_drive_link_not_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    body = {"links": [{"local_file_name": "report.docx", "drive_file_id": "file1", "drive_file_name": "Report.docx", "mime_type": "text/plain"}]}
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/link", headers=auth_headers, json=body)
    assert res.status_code == 400
    assert "Failed to link" in res.json()["detail"]

def test_drive_link_requires_auth(client, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    body = {"links": [{"local_file_name": "report.docx", "drive_file_id": "file1", "drive_file_name": "Report.docx", "mime_type": "text/plain"}]}
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/link", json=body)
    assert res.status_code == 401

def test_drive_link_upload_not_found(client, auth_headers):
    body = {"links": [{"local_file_name": "report.docx", "drive_file_id": "file1", "drive_file_name": "Report.docx", "mime_type": "text/plain"}]}
    res = client.post("/projects/upload/999/projects/TestProject/drive/link", headers=auth_headers, json=body)
    assert res.status_code == 404

def test_drive_link_empty_links(client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    with patch("src.services.google_drive_service.get_google_drive_token") as mock_get_token:
        mock_get_token.return_value = "ya29.token123"
        res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/drive/link", headers=auth_headers, json={"links": []})
        assert res.status_code == 200
        assert res.json()["data"]["files_linked"] == 0
