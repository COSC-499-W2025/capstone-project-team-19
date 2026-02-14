from .test_uploads_file_roles import (
    _advance_to_needs_file_roles,
    _cleanup_upload_artifacts,
    _get_project_key,
)
from .test_uploads_wizard import _make_zip_bytes


PROJECT = "ProjectA"


def _build_single_project_zip(project_name: str = PROJECT) -> bytes:
    return _make_zip_bytes(
        {
            f"{project_name}/main_report.txt": "Main report content",
            f"{project_name}/support.txt": "Supporting content",
        }
    )


def _get_upload_state(client, auth_headers, upload_id: int) -> dict:
    res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 200
    return (res.json().get("data") or {}).get("state") or {}


def test_post_key_role_happy_path_persists_normalized_value(client, auth_headers):
    upload = _advance_to_needs_file_roles(client, auth_headers, _build_single_project_zip())
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = _get_project_key(state, PROJECT)

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/key-role",
        headers=auth_headers,
        json={"key_role": "  Backend   Developer  "},
    )
    assert res.status_code == 200
    body_state = (res.json().get("data") or {}).get("state") or {}
    contrib = ((body_state.get("contributions") or {}).get(PROJECT)) or {}
    assert contrib.get("key_role") == "Backend Developer"

    persisted_state = _get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = ((persisted_state.get("contributions") or {}).get(PROJECT)) or {}
    assert persisted_contrib.get("key_role") == "Backend Developer"

    _cleanup_upload_artifacts(persisted_state)


def test_post_key_role_returns_404_for_unknown_project_key(client, auth_headers):
    upload = _advance_to_needs_file_roles(client, auth_headers, _build_single_project_zip())
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = _get_project_key(state, PROJECT)

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key + 999}/key-role",
        headers=auth_headers,
        json={"key_role": "Backend Developer"},
    )
    assert res.status_code == 404

    persisted_state = _get_upload_state(client, auth_headers, upload_id)
    _cleanup_upload_artifacts(persisted_state)


def test_post_key_role_returns_409_when_upload_not_ready(client, auth_headers):
    zip_bytes = _make_zip_bytes(
        {
            "ProjectA/readme.txt": "hello from A",
            "ProjectB/readme.txt": "hello from B",
        }
    )
    start = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("two_projects.zip", zip_bytes, "application/zip")},
    )
    assert start.status_code == 200
    upload = start.json()["data"]
    upload_id = upload["upload_id"]

    if upload["status"] == "needs_dedup":
        asks = (upload.get("state") or {}).get("dedup_asks") or {}
        decisions = {k: "new_project" for k in asks.keys()}
        resolved = client.post(
            f"/projects/upload/{upload_id}/dedup/resolve",
            headers=auth_headers,
            json={"decisions": decisions},
        )
        assert resolved.status_code == 200
        upload = resolved.json()["data"]

    assert upload["status"] in {"needs_classification", "needs_project_types"}
    state = upload.get("state") or {}
    project_key = _get_project_key(state, "ProjectA")

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/key-role",
        headers=auth_headers,
        json={"key_role": "Backend Developer"},
    )
    assert res.status_code == 409

    _cleanup_upload_artifacts((upload.get("state") or {}))


def test_post_key_role_accepts_blank_and_clears_value(client, auth_headers):
    upload = _advance_to_needs_file_roles(client, auth_headers, _build_single_project_zip())
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = _get_project_key(state, PROJECT)

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/key-role",
        headers=auth_headers,
        json={"key_role": "   "},
    )
    assert res.status_code == 200
    body_state = (res.json().get("data") or {}).get("state") or {}
    contrib = ((body_state.get("contributions") or {}).get(PROJECT)) or {}
    assert contrib.get("key_role") == ""

    persisted_state = _get_upload_state(client, auth_headers, upload_id)
    persisted_contrib = ((persisted_state.get("contributions") or {}).get(PROJECT)) or {}
    assert persisted_contrib.get("key_role") == ""
    _cleanup_upload_artifacts(persisted_state)
