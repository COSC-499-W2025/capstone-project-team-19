import shutil
from pathlib import Path
import pytest
import src.db as db
from src.utils.parsing import ZIP_DATA_DIR
from test_uploads_wizard import client, _seed_user, _make_zip_bytes


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
        # Don't fail tests because cleanup didn't happen
        pass


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
        "version_files",
        "project_versions",
        "projects",
        "project_classifications",
        "files",
        "uploads",
        "users",
    ]:
        if _table_exists(conn, table):
            conn.execute(f"DELETE FROM {table};")

    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def _fresh_state():
    _reset_db_safely()
    _seed_user(1)
    yield
    _reset_db_safely()


def test_upload_exact_duplicate_is_skipped_and_fails_if_all_projects_skipped():
    zip1 = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res1 = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("p1.zip", zip1, "application/zip")},
    )
    assert res1.status_code == 200
    body1 = res1.json()
    assert body1["success"] is True
    _cleanup_upload_artifacts((body1.get("data") or {}).get("state") or {})

    zip2 = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res2 = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("p1_dup.zip", zip2, "application/zip")},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True

    upload2 = body2["data"]
    assert upload2["status"] == "failed"
    state2 = upload2.get("state") or {}
    assert "ProjectA" in (state2.get("dedup_skipped_projects") or [])

    _cleanup_upload_artifacts(state2)


def test_upload_loose_match_triggers_needs_dedup_and_resolve_new_version_advances():
    zip1 = _make_zip_bytes({"ProjectA/readme.txt": "same-content"})
    res1 = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("base.zip", zip1, "application/zip")},
    )
    assert res1.status_code == 200
    body1 = res1.json()
    assert body1["success"] is True
    _cleanup_upload_artifacts((body1.get("data") or {}).get("state") or {})

    zip2 = _make_zip_bytes({"ProjectA/renamed.txt": "same-content"})
    res2 = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("variant.zip", zip2, "application/zip")},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True

    upload2 = body2["data"]
    assert upload2["status"] == "needs_dedup"
    state2 = upload2.get("state") or {}
    asks = state2.get("dedup_asks") or {}
    assert "ProjectA" in asks

    upload_id = upload2["upload_id"]
    resolve_res = client.post(
        f"/projects/upload/{upload_id}/dedup/resolve",
        headers={"X-User-Id": "1"},
        json={"decisions": {"ProjectA": "new_version"}},
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()["data"]

    assert resolved["status"] != "needs_dedup"
    resolved_state = resolved.get("state") or {}
    assert (resolved_state.get("dedup_asks") or {}) == {}
    assert (resolved_state.get("dedup_resolved") or {}).get("ProjectA") == "new_version"

    _cleanup_upload_artifacts(state2)
    _cleanup_upload_artifacts(resolved_state)

