from src.api.auth.security import create_access_token

from .conftest import TEST_JWT_SECRET
from .test_uploads_file_roles import _advance_to_needs_file_roles
from .test_uploads_wizard import _make_zip_bytes


def _create_upload(client, auth_headers) -> int:
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    return int(res.json()["data"]["upload_id"])


def test_upload_run_requires_auth(client):
    res = client.post("/projects/upload/1/run", json={"scope": "all"})
    assert res.status_code == 401


def test_upload_run_rejects_non_ready_status(client, auth_headers):
    upload_id = _create_upload(client, auth_headers)

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all"},
    )
    assert res.status_code == 409
    assert "Upload not ready for run" in res.json()["detail"]


def test_upload_run_contract_happy_path_ready_code_upload(client, auth_headers):
    # code-only upload can be run without file_roles.main_file
    zip_bytes = _make_zip_bytes({"ProjectA/main.py": "print('hi')\n"})
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all", "force_rerun": False},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["upload_id"] == upload_id
    assert data["scope"] == "all"
    assert data["accepted"] is True
    assert "Context prepared for 1 project(s)." in data["message"]


def test_upload_run_ownership_check_returns_404(client, auth_headers, consent_user_id_2):
    upload_id = _create_upload(client, auth_headers)

    token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=consent_user_id_2,
        username="new-user",
        expires_minutes=60,
    )
    auth_headers_user_2 = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers_user_2,
        json={"scope": "all"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Upload not found"


def test_upload_run_rejects_text_project_without_main_file(client, auth_headers):
    # text upload reaches needs_file_roles but main file has not been selected yet.
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]

    res = client.post(
        f"/projects/upload/{upload_id}/run",
        headers=auth_headers,
        json={"scope": "all"},
    )
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert detail["message"] == "Upload state is incomplete for analysis run"
    assert any(err.get("code") == "missing_main_file" for err in detail.get("errors", []))
