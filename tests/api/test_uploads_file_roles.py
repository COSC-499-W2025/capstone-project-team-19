import shutil
from pathlib import Path
import pytest

import src.db as db
from src.utils.parsing import ZIP_DATA_DIR

# reuse these from your existing tests
from test_uploads_wizard import client, _seed_user, _make_zip_bytes


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _reset_db_safely() -> None:
    conn = db.connect()
    conn.execute("PRAGMA foreign_keys=ON;")

    for table in [
        "project_classifications",
        "files",
        "uploads",
        "users",
    ]:
        if _table_exists(conn, table):
            conn.execute(f"DELETE FROM {table};")

    conn.commit()
    conn.close()


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


@pytest.fixture(autouse=True)
def _fresh_state():
    _reset_db_safely()
    _seed_user(1)
    yield
    _reset_db_safely()


def _advance_to_needs_file_roles(zip_bytes: bytes) -> dict:
    """
    Start upload, then advance through classification / project-types if needed,
    until we reach needs_file_roles.
    """
    res = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    upload = res.json()["data"]
    upload_id = upload["upload_id"]

    # If it needs classification, submit it
    if upload["status"] == "needs_classification":
        res2 = client.post(
            f"/projects/upload/{upload_id}/classifications",
            headers={"X-User-Id": "1"},
            json={"assignments": {"ProjectA": "individual"}},
        )
        assert res2.status_code == 200
        upload = res2.json()["data"]

    # If it needs project types, choose text for this test zip
    if upload["status"] == "needs_project_types":
        res3 = client.post(
            f"/projects/upload/{upload_id}/project-types",
            headers={"X-User-Id": "1"},
            json={"project_types": {"ProjectA": "text"}},
        )
        assert res3.status_code == 200
        upload = res3.json()["data"]

    assert upload["status"] == "needs_file_roles"
    return upload


def test_list_project_files_requires_needs_file_roles():
    # Use 2 projects so it reliably lands in needs_classification first
    zip_bytes = _make_zip_bytes(
        {
            "ProjectA/readme.txt": "hello",
            "ProjectB/readme.txt": "hello",
        }
    )
    start = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("two_projects.zip", zip_bytes, "application/zip")},
    )
    assert start.status_code == 200
    upload = start.json()["data"]
    upload_id = upload["upload_id"]

    # Not in needs_file_roles yet -> should 409
    res = client.get(
        f"/projects/upload/{upload_id}/projects/ProjectA/files",
        headers={"X-User-Id": "1"},
    )
    assert res.status_code == 409

    _cleanup_upload_artifacts((upload.get("state") or {}))


def test_list_files_then_set_main_file_happy_path():
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    upload = _advance_to_needs_file_roles(zip_bytes)
    upload_id = upload["upload_id"]

    # (5) list files
    res = client.get(
        f"/projects/upload/{upload_id}/projects/ProjectA/files",
        headers={"X-User-Id": "1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    data = body["data"]
    assert data["project_name"] == "ProjectA"
    assert len(data["all_files"]) >= 1

    # choose a relpath to set as main file (prefer text_files)
    chosen = None
    if data.get("text_files"):
        chosen = data["text_files"][0]["relpath"]
    else:
        chosen = data["all_files"][0]["relpath"]

    assert isinstance(chosen, str) and chosen

    # (6) set main file
    res2 = client.post(
        f"/projects/upload/{upload_id}/projects/ProjectA/main-file",
        headers={"X-User-Id": "1"},
        json={"relpath": chosen},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True

    state = body2["data"].get("state") or {}
    assert state["file_roles"]["ProjectA"]["main_file"] == chosen

    _cleanup_upload_artifacts(state)


def test_set_main_file_rejects_unsafe_relpath():
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    upload = _advance_to_needs_file_roles(zip_bytes)
    upload_id = upload["upload_id"]

    res = client.post(
        f"/projects/upload/{upload_id}/projects/ProjectA/main-file",
        headers={"X-User-Id": "1"},
        json={"relpath": "../evil.txt"},
    )
    assert res.status_code == 422

    _cleanup_upload_artifacts((upload.get("state") or {}))
