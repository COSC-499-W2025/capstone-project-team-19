import shutil
from pathlib import Path

import pytest
from src.utils.parsing import ZIP_DATA_DIR

# reuse this helper from existing tests
from .test_uploads_wizard import _make_zip_bytes


def _get_project_key(state: dict, project_name: str) -> int:
    pk = (state.get("dedup_project_keys") or {}).get(project_name)
    assert pk is not None, f"project_key not found for {project_name}"
    return int(pk)


def _cleanup_upload_artifacts(upload_state: dict) -> None:
    zip_path = (upload_state or {}).get("zip_path")
    if not zip_path:
        return

    try:
        zp = Path(zip_path)
        extract_dir = Path(ZIP_DATA_DIR) / zp.stem
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        if zp.exists():
            zp.unlink(missing_ok=True)
    except Exception:
        pass


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


@pytest.fixture(autouse=True)
def _fresh_state(seed_conn):
    """
    Keep this module isolated so dedup doesn't accidentally trigger across tests.
    """
    seed_conn.execute("PRAGMA foreign_keys=ON;")

    # delete in FK-safe-ish order (only if tables exist)
    for table in [
        "version_files",
        "project_versions",
        "projects",
        "files",
        "uploads",
        "users",
    ]:
        if _table_exists(seed_conn, table):
            seed_conn.execute(f"DELETE FROM {table};")

    # re-seed user 1 for JWT-auth tests
    if _table_exists(seed_conn, "users"):
        seed_conn.execute(
            "INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?)",
            (1, "test-user"),
        )

    seed_conn.commit()
    yield


def _advance_to_needs_file_roles(client, auth_headers, zip_bytes: bytes) -> dict:
    """
    Start upload, then advance through dedup/classification/project-types (if needed)
    until we reach needs_file_roles.
    """
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    upload = res.json()["data"]
    upload_id = upload["upload_id"]

    # If dedup needs resolving, default to "new_project" for all asked projects
    if upload["status"] == "needs_dedup":
        asks = (upload.get("state") or {}).get("dedup_asks") or {}
        decisions = {k: "new_project" for k in asks.keys()}
        res_d = client.post(
            f"/projects/upload/{upload_id}/dedup/resolve",
            headers=auth_headers,
            json={"decisions": decisions},
        )
        assert res_d.status_code == 200
        upload = res_d.json()["data"]

    # If it needs classification, classify all known projects as individual (keeps test simple)
    if upload["status"] == "needs_classification":
        layout = (upload.get("state") or {}).get("layout") or {}
        known = set(layout.get("pending_projects") or []) | set((layout.get("auto_assignments") or {}).keys())
        assignments = {p: "individual" for p in known} or {"ProjectA": "individual"}

        res2 = client.post(
            f"/projects/upload/{upload_id}/classifications",
            headers=auth_headers,
            json={"assignments": assignments},
        )
        assert res2.status_code == 200
        upload = res2.json()["data"]

    # If it needs project types, choose text for all required keys (mixed + unknown)
    if upload["status"] == "needs_project_types":
        state = upload.get("state") or {}
        needs = set(state.get("project_types_mixed") or []) | set(state.get("project_types_unknown") or [])
        project_types = {p: "text" for p in needs} or {"ProjectA": "text"}

        res3 = client.post(
            f"/projects/upload/{upload_id}/project-types",
            headers=auth_headers,
            json={"project_types": project_types},
        )
        assert res3.status_code == 200
        upload = res3.json()["data"]

    assert upload["status"] == "needs_file_roles"
    return upload


def test_list_project_files_requires_needs_file_roles(client, auth_headers):
    # Two projects -> reliably lands in needs_classification (not needs_file_roles)
    zip_bytes = _make_zip_bytes(
        {
            "ProjectA/readme.txt": "hello but it's A and is different",
            "ProjectB/readme.txt": "hello and I am B, I am not similar to A",
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

    # Not in needs_file_roles yet -> should 409
    state = upload.get("state") or {}
    project_key = _get_project_key(state, "ProjectA")
    res = client.get(
        f"/projects/upload/{upload_id}/projects/{project_key}/files",
        headers=auth_headers,
    )
    assert res.status_code == 409

    _cleanup_upload_artifacts(state)


def test_list_files_then_set_main_file_happy_path(client, auth_headers):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = _get_project_key(state, "ProjectA")

    # (5) list files
    res = client.get(
        f"/projects/upload/{upload_id}/projects/{project_key}/files",
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["project_name"] == "ProjectA"
    assert len(data["all_files"]) >= 1

    # choose a relpath to set as main file (prefer text_files)
    chosen = (data.get("text_files") or data["all_files"])[0]["relpath"]
    assert isinstance(chosen, str) and chosen

    # (6) set main file
    res2 = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/main-file",
        headers=auth_headers,
        json={"relpath": chosen},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True

    state = body2["data"].get("state") or {}
    assert state["file_roles"]["ProjectA"]["main_file"] == chosen

    _cleanup_upload_artifacts(state)


def test_set_main_file_rejects_unsafe_relpath(client, auth_headers):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    upload = _advance_to_needs_file_roles(client, auth_headers, zip_bytes)
    upload_id = upload["upload_id"]
    state = upload.get("state") or {}
    project_key = _get_project_key(state, "ProjectA")

    res = client.post(
        f"/projects/upload/{upload_id}/projects/{project_key}/main-file",
        headers=auth_headers,
        json={"relpath": "../evil.txt"},
    )
    assert res.status_code == 422

    _cleanup_upload_artifacts((upload.get("state") or {}))
