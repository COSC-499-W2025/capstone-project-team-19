import shutil
from pathlib import Path

from src.api.auth.security import create_access_token
from src.utils.parsing import ZIP_DATA_DIR

from .conftest import TEST_JWT_SECRET
from .test_uploads_wizard import _make_zip_bytes


def _cleanup_artifacts_from_state(upload_state: dict) -> None:
    zip_path = (upload_state or {}).get("zip_path")
    if not zip_path:
        return

    try:
        zip_file = Path(zip_path)
        extract_dir = Path(ZIP_DATA_DIR) / zip_file.stem
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        if zip_file.exists():
            zip_file.unlink(missing_ok=True)
    except Exception:
        pass


def _start_upload(client, auth_headers, files: dict[str, str], filename: str = "test.zip") -> dict:
    zip_bytes = _make_zip_bytes(files)
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": (filename, zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    return body["data"]


def _advance_to_needs_file_roles(client, auth_headers, upload: dict) -> dict:
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

    if upload["status"] == "needs_classification":
        layout = (upload.get("state") or {}).get("layout") or {}
        known = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
        assignments = {p: "individual" for p in known} or {"ProjectA": "individual"}
        classified = client.post(
            f"/projects/upload/{upload_id}/classifications",
            headers=auth_headers,
            json={"assignments": assignments},
        )
        assert classified.status_code == 200
        upload = classified.json()["data"]

    if upload["status"] == "needs_project_types":
        state = upload.get("state") or {}
        needs = set(state.get("project_types_mixed") or []) | set(state.get("project_types_unknown") or [])
        project_types = {p: "text" for p in needs} or {"ProjectA": "text"}
        typed = client.post(
            f"/projects/upload/{upload_id}/project-types",
            headers=auth_headers,
            json={"project_types": project_types},
        )
        assert typed.status_code == 200
        upload = typed.json()["data"]

    assert upload["status"] == "needs_file_roles"
    return upload


def test_cancel_upload_deletes_db_rows_and_disk_artifacts(client, auth_headers, seed_conn):
    upload = _start_upload(client, auth_headers, {"ProjectA/readme.txt": "hello"})
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    zip_path = state.get("zip_path")
    assert zip_path

    zip_file = Path(zip_path)
    extract_dir = Path(ZIP_DATA_DIR) / zip_file.stem
    assert zip_file.exists()
    assert extract_dir.exists()

    project_exists_before = seed_conn.execute(
        "SELECT 1 FROM projects WHERE user_id = 1 AND display_name = ? LIMIT 1",
        ("ProjectA",),
    ).fetchone()
    assert project_exists_before is not None

    delete_res = client.delete(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert delete_res.status_code == 200
    delete_body = delete_res.json()
    assert delete_body["success"] is True
    assert delete_body["data"] is None

    status_res = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert status_res.status_code == 404

    upload_row = seed_conn.execute(
        "SELECT 1 FROM uploads WHERE upload_id = ?",
        (upload_id,),
    ).fetchone()
    assert upload_row is None

    versions_count = seed_conn.execute(
        "SELECT COUNT(*) FROM project_versions WHERE upload_id = ?",
        (upload_id,),
    ).fetchone()[0]
    assert int(versions_count) == 0

    project_exists_after = seed_conn.execute(
        "SELECT 1 FROM projects WHERE user_id = 1 AND display_name = ? LIMIT 1",
        ("ProjectA",),
    ).fetchone()
    assert project_exists_after is None

    assert not zip_file.exists()
    assert not extract_dir.exists()


def test_cancel_upload_is_forbidden_for_done_status(client, auth_headers, seed_conn):
    upload = _start_upload(client, auth_headers, {"ProjectA/readme.txt": "hello"})
    upload_id = upload["upload_id"]

    seed_conn.execute("UPDATE uploads SET status = 'done' WHERE upload_id = ?", (upload_id,))
    seed_conn.commit()

    res = client.delete(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res.status_code == 409
    assert "cannot be cancelled" in str(res.json().get("detail", "")).lower()

    _cleanup_artifacts_from_state(upload.get("state") or {})


def test_cancel_upload_returns_404_for_non_owner(client, auth_headers, consent_user_id_2):
    upload = _start_upload(client, auth_headers, {"ProjectA/readme.txt": "hello"})
    upload_id = upload["upload_id"]

    other_user_token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=consent_user_id_2,
        username="new-user",
        expires_minutes=60,
    )
    other_headers = {"Authorization": f"Bearer {other_user_token}"}

    res = client.delete(f"/projects/upload/{upload_id}", headers=other_headers)
    assert res.status_code == 404

    cleanup = client.delete(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert cleanup.status_code == 200


def test_reupload_after_cancel_can_still_list_project_files(client, auth_headers):
    files = {"ProjectA/readme.txt": "hello again"}
    first = _start_upload(client, auth_headers, files, filename="same.zip")
    first_id = first["upload_id"]

    cancel_res = client.delete(f"/projects/upload/{first_id}", headers=auth_headers)
    assert cancel_res.status_code == 200

    second = _start_upload(client, auth_headers, files, filename="same.zip")
    second = _advance_to_needs_file_roles(client, auth_headers, second)
    second_id = second["upload_id"]
    state = second.get("state") or {}
    project_key = (state.get("dedup_project_keys") or {}).get("ProjectA")
    assert isinstance(project_key, int)

    files_res = client.get(
        f"/projects/upload/{second_id}/projects/{project_key}/files",
        headers=auth_headers,
    )
    assert files_res.status_code == 200
    files_body = files_res.json()
    assert files_body["success"] is True
    assert len(files_body["data"]["all_files"]) > 0

    cleanup = client.delete(f"/projects/upload/{second_id}", headers=auth_headers)
    assert cleanup.status_code == 200
