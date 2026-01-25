import json
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.main import app
import src.db as db

client = TestClient(app)

def _seed_user(user_id: int = 1):
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES (?, 'test-user')", (user_id,))
    conn.commit()
    conn.close()

def _create_test_upload(user_id: int = 1) -> int:
    conn = db.connect()
    db.init_schema(conn)
    _seed_user(user_id)
    cursor = conn.execute("INSERT INTO uploads (user_id, status, state_json) VALUES (?, 'needs_classification', '{\"layout\": {\"pending_projects\": [\"TestProject\"]}}')", (user_id,))
    conn.commit()
    upload_id = cursor.lastrowid
    conn.close()
    return upload_id

def _setup_oauth_state(upload_id: int, oauth_state: str, project_name: str = "TestProject"):
    conn = db.connect()
    conn.execute("UPDATE uploads SET state_json = ? WHERE upload_id = ?", (json.dumps({f"github_{project_name}": {"oauth_state": oauth_state, "user_id": 1, "upload_id": upload_id, "project_name": project_name}}), upload_id))
    conn.commit()
    conn.close()

# TESTS 

def test_github_start_requires_user_header():
    res = client.post("/projects/upload/1/projects/TestProject/github/start", json={"connect_now": True})
    assert res.status_code == 401

def test_github_start_connect_now_false():
    _seed_user(1)
    upload_id = _create_test_upload(1)
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers={"X-User-Id": "1"}, json={"connect_now": False})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.generate_github_auth_url")
def test_github_start_connect_now_true_generates_url(mock_auth_url, mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = None
    mock_auth_url.return_value = "https://github.com/login/oauth/authorize?state=abc123"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers={"X-User-Id": "1"}, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] == "https://github.com/login/oauth/authorize?state=abc123"
    mock_auth_url.assert_called_once()

@patch("src.services.github_service.get_github_token")
def test_github_start_already_connected(mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = "existing_token"
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/start", headers={"X-User-Id": "1"}, json={"connect_now": True})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["auth_url"] is None

def test_github_start_upload_not_found():
    _seed_user(1)
    res = client.post("/projects/upload/999/projects/TestProject/github/start", headers={"X-User-Id": "1"}, json={"connect_now": True})
    assert res.status_code == 404

@patch("src.services.github_service.exchange_code_for_token")
@patch("src.services.github_service.save_github_token")
def test_github_callback_success(mock_save_token, mock_exchange):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    _setup_oauth_state(upload_id, "test_state_123")
    mock_exchange.return_value = {"access_token": "token123"}
    res = client.get("/auth/github/callback?code=abc123&state=test_state_123")
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_save_token.assert_called_once()
    call_args = mock_save_token.call_args[0]
    assert call_args[1] == 1
    assert call_args[2] == "token123"

def test_github_callback_missing_code():
    res = client.get("/auth/github/callback?state=test")
    assert res.status_code == 422

def test_github_callback_invalid_state():
    _seed_user(1)
    with patch("src.services.github_service._find_upload_by_oauth_state") as mock_find:
        mock_find.return_value = None
        res = client.get("/auth/github/callback?code=abc123&state=invalid")
        assert res.status_code == 400
        assert "Invalid OAuth state" in res.json()["detail"]

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.list_user_repos")
def test_github_repos_success(mock_list_repos, mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = "token123"
    mock_list_repos.return_value = ["owner/repo1", "owner/repo2"]
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/github/repos", headers={"X-User-Id": "1"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]["repos"]) == 2
    assert res.json()["data"]["repos"][0]["full_name"] == "owner/repo1"

@patch("src.services.github_service.get_github_token")
def test_github_repos_not_connected(mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = None
    res = client.get(f"/projects/upload/{upload_id}/projects/TestProject/github/repos", headers={"X-User-Id": "1"})
    assert res.status_code == 401
    assert "not connected" in res.json()["detail"].lower()

@patch("src.services.github_service.get_github_token")
@patch("src.services.github_service.get_github_repo_metadata")
@patch("src.services.github_service.save_project_repo")
def test_github_link_success(mock_save_repo, mock_get_metadata, mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = "token123"
    mock_get_metadata.return_value = ("https://github.com/owner/repo", "owner", "repo", 12345, "main")
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers={"X-User-Id": "1"}, json={"repo_full_name": "owner/repo"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["repo_full_name"] == "owner/repo"
    mock_save_repo.assert_called_once()

@patch("src.services.github_service.get_github_token")
def test_github_link_not_connected(mock_get_token):
    _seed_user(1)
    upload_id = _create_test_upload(1)
    mock_get_token.return_value = None
    res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers={"X-User-Id": "1"}, json={"repo_full_name": "owner/repo"})
    assert res.status_code == 400
    assert "Failed to link" in res.json()["detail"]

def test_github_link_invalid_repo_format():
    _seed_user(1)
    upload_id = _create_test_upload(1)
    with patch("src.services.github_service.get_github_token") as mock_get_token:
        mock_get_token.return_value = "token123"
        res = client.post(f"/projects/upload/{upload_id}/projects/TestProject/github/link", headers={"X-User-Id": "1"}, json={"repo_full_name": "invalid-format"})
        assert res.status_code == 400
        assert "Failed to link" in res.json()["detail"]