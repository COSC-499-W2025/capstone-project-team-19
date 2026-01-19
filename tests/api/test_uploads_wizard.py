import io
import zipfile

from fastapi.testclient import TestClient

from src.api.main import app
import src.db as db

client = TestClient(app)


def _seed_user(user_id: int = 1):
    conn = db.connect()
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username) VALUES (?, 'test-user')",
        (user_id,),
    )
    conn.commit()
    conn.close()


def _make_zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            z.writestr(path, content)
    return buf.getvalue()


def test_upload_requires_user_header():
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 401


def test_upload_invalid_user_is_404():
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        headers={"X-User-Id": "999"},
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_upload_start_and_get_status():
    _seed_user(1)

    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    upload = body["data"]
    assert "upload_id" in upload
    upload_id = upload["upload_id"]
    assert upload["status"] in {"needs_classification", "failed"}

    # GET upload status
    res2 = client.get(f"/projects/upload/{upload_id}", headers={"X-User-Id": "1"})
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True
    assert body2["data"]["upload_id"] == upload_id


def test_submit_classifications_validates_values():
    _seed_user(1)

    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    start = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    ).json()
    upload_id = start["data"]["upload_id"]

    # invalid classification
    bad = client.post(
        f"/projects/upload/{upload_id}/classifications",
        headers={"X-User-Id": "1"},
        json={"assignments": {"ProjectA": "solo"}},
    )
    assert bad.status_code == 422

    # valid classification
    ok = client.post(
        f"/projects/upload/{upload_id}/classifications",
        headers={"X-User-Id": "1"},
        json={"assignments": {"ProjectA": "individual"}},
    )
    assert ok.status_code == 200
    ok_body = ok.json()
    assert ok_body["success"] is True
    assert ok_body["data"]["state"]["classifications"]["ProjectA"] == "individual"

    # verify DB write exists
    conn = db.connect()
    row = conn.execute(
        """
        SELECT classification
        FROM project_classifications
        WHERE user_id = 1 AND project_name = 'ProjectA'
        """,
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "individual"


def test_submit_project_types_unknown_project_is_422():
    _seed_user(1)

    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    start = client.post(
        "/projects/upload",
        headers={"X-User-Id": "1"},
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    ).json()
    upload_id = start["data"]["upload_id"]

    # Unknown project key should 422
    res = client.post(
        f"/projects/upload/{upload_id}/project-types",
        headers={"X-User-Id": "1"},
        json={"project_types": {"NotAProject": "text"}},
    )
    assert res.status_code == 422
