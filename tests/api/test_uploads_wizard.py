import io
import zipfile
import pytest

from src.api.auth.security import create_access_token
from .conftest import TEST_JWT_SECRET


def _make_zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            z.writestr(path, content)
    return buf.getvalue()


def test_upload_requires_user_header(client):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 401


def test_upload_invalid_user_is_404(client, auth_headers_nonexistent_user):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        headers=auth_headers_nonexistent_user,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_upload_start_and_get_status(client, auth_headers):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
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
    res2 = client.get(f"/projects/upload/{upload_id}", headers=auth_headers)
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["success"] is True
    assert body2["data"]["upload_id"] == upload_id


def test_submit_classifications_validates_values(client, auth_headers, seed_conn):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    start = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    ).json()
    upload_id = start["data"]["upload_id"]

    # invalid classification
    bad = client.post(
        f"/projects/upload/{upload_id}/classifications",
        headers=auth_headers,
        json={"assignments": {"ProjectA": "solo"}},
    )
    assert bad.status_code == 422

    # valid classification
    ok = client.post(
        f"/projects/upload/{upload_id}/classifications",
        headers=auth_headers,
        json={"assignments": {"ProjectA": "individual"}},
    )
    assert ok.status_code == 200
    ok_body = ok.json()
    assert ok_body["success"] is True
    assert ok_body["data"]["state"]["classifications"]["ProjectA"] == "individual"

    # verify DB write exists
    row = seed_conn.execute(
        """
        SELECT classification
        FROM project_classifications
        WHERE user_id = 1 AND project_name = 'ProjectA'
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == "individual"


def test_submit_project_types_unknown_project_is_422(client, auth_headers):
    zip_bytes = _make_zip_bytes({"ProjectA/readme.txt": "hello"})
    start = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", zip_bytes, "application/zip")},
    ).json()
    upload_id = start["data"]["upload_id"]

    # Unknown project key should 422
    res = client.post(
        f"/projects/upload/{upload_id}/project-types",
        headers=auth_headers,
        json={"project_types": {"NotAProject": "text"}},
    )
    assert res.status_code == 422
