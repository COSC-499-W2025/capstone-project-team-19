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

def _setup_oauth_state(seed_conn, upload_id: int, oauth_state: str, project_name: str = "TestProject"):
    seed_conn.execute(
        "UPDATE uploads SET state_json = ? WHERE upload_id = ?",
        (json.dumps({f"github_{project_name}": {"oauth_state": oauth_state, "user_id": 1, "upload_id": upload_id, "project_name": project_name}}), upload_id)
    )
    seed_conn.commit()

def test_github_start_requires_auth(client):
    res = client.post("/projects/upload/1/projects/TestProject/github/start", json={"connect_now": True})
    assert res.status_code == 401

def test_github_start_connect_now_false(client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers=auth_headers, json={"connect_now": False})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.generate_github_auth_url")
def test_github_start_connect_now_true_generates_url(mock_auth_url, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    mock_auth_url.return_value = "https://github.com/login/oauth/authorize?state=abc123"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] == "https://github.com/login/oauth/authorize?state=abc123"
    mock_auth_url.assert_called_once()

@patch("src.services.github_service.get_github_token")
def test_github_start_already_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "existing_token"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

def test_github_start_upload_not_found(client, auth_headers):
    res = client.post("/projects/upload/999/projects/TestProject/github/start", headers=auth_headers, json={"connect_now": True})
    assert res.status_code == 404

@patch("src.services.github_service.exchange_code_for_token")
@patch("src.services.github_service.save_github_token")
def test_github_callback_success(mock_save_token, mock_exchange, client, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    _setup_oauth_state(seed_conn, upload_id, "test_state_123")
    mock_exchange.return_value = {"access_token": "token123"}
    res = client.get("/auth/github/callback?code=abc123&state=test_state_123")
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_save_token.assert_called_once()
    call_args = mock_save_token.call_args[0]
    assert call_args[1] == 1
    assert call_args[2] == "token123"

def test_github_callback_missing_code(client):
    res = client.get("/auth/github/callback?state=test")
    assert res.status_code == 422

def test_github_callback_invalid_state(client, seed_conn):
    _create_test_upload(seed_conn, 1)
    with patch("src.services.github_service._find_upload_by_oauth_state") as mock_find:
        mock_find.return_value = None
        res = client.get("/auth/github/callback?code=abc123&state=invalid")
        assert res.status_code == 400
        assert "Invalid OAuth state" in res.json()["detail"]

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.list_user_repos")
def test_github_repos_success(mock_list_repos, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "token123"
    mock_list_repos.return_value = ["owner/repo1", "owner/repo2"]
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/github/repos", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]["repos"]) == 2
    assert res.json()["data"]["repos"][0]["full_name"] == "owner/repo1"

@patch("src.services.github_service.get_github_token")
def test_github_repos_not_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/github/repos", headers=auth_headers)
    assert res.status_code == 401
    assert "not connected" in res.json()["detail"].lower()

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.get_github_repo_metadata")
@patch("src.services.github_service.save_project_repo")
def test_github_link_success(mock_save_repo, mock_get_metadata, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "token123"
    mock_get_metadata.return_value = ("https://github.com/owner/repo", "owner", "repo", 12345, "main")
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers=auth_headers, json={"repo_full_name": "owner/repo"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["repo_full_name"] == "owner/repo"
    mock_save_repo.assert_called_once()

@patch("src.services.github_service.get_github_token")
def test_github_link_not_connected(mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = None
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers=auth_headers, json={"repo_full_name": "owner/repo"})
    assert res.status_code == 400
    assert "Failed to link" in res.json()["detail"]

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.get_github_repo_metadata")
def test_github_link_invalid_repo_format(mock_get_metadata, mock_get_token, client, auth_headers, seed_conn):
    upload_id = _create_test_upload(seed_conn, 1)
    mock_get_token.return_value = "token123"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers=auth_headers, json={"repo_full_name": "invalid-format"})
    assert res.status_code == 400
    assert "Failed to link" in res.json()["detail"]