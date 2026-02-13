import io

import pytest
from PIL import Image

from src.api.auth.security import create_access_token
from tests.api.conftest import seed_project
import src.services.thumbnails_service as thumbnails_service


def _create_test_image(fmt: str = "PNG", size: tuple = (100, 100)) -> io.BytesIO:
    img = Image.new("RGB", size, color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


@pytest.fixture(autouse=True)
def _patch_images_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(thumbnails_service, "IMAGES_DIR", tmp_path / "images")


# ── Auth required ────────────────────────────────────────────────────

def test_upload_requires_auth(client):
    res = client.post("/projects/1/thumbnail")
    assert res.status_code == 401


def test_get_requires_auth(client):
    res = client.get("/projects/1/thumbnail")
    assert res.status_code == 401


def test_delete_requires_auth(client):
    res = client.delete("/projects/1/thumbnail")
    assert res.status_code == 401


# ── Project not found ────────────────────────────────────────────────

def test_upload_project_not_found(client, auth_headers):
    buf = _create_test_image()
    res = client.post(
        "/projects/999999/thumbnail",
        headers=auth_headers,
        files={"file": ("test.png", buf, "image/png")},
    )
    assert res.status_code == 404
    assert "Project not found" in res.json()["detail"]


def test_get_project_not_found(client, auth_headers):
    res = client.get("/projects/999999/thumbnail", headers=auth_headers)
    assert res.status_code == 404
    assert "Project not found" in res.json()["detail"]


def test_delete_project_not_found(client, auth_headers):
    res = client.delete("/projects/999999/thumbnail", headers=auth_headers)
    assert res.status_code == 404
    assert "Project not found" in res.json()["detail"]


# ── Invalid image upload ─────────────────────────────────────────────

def test_upload_invalid_image(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "InvalidImgProject")
    bad_bytes = io.BytesIO(b"not an image at all")
    res = client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("bad.png", bad_bytes, "image/png")},
    )
    assert res.status_code == 422


# ── Upload success ───────────────────────────────────────────────────

def test_upload_png_success(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "PngProject")
    buf = _create_test_image("PNG")
    res = client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("photo.png", buf, "image/png")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["project_id"] == project_id
    assert body["data"]["project_name"] == "PngProject"


def test_upload_jpg_success(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "JpgProject")
    buf = _create_test_image("JPEG")
    res = client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("photo.jpg", buf, "image/jpeg")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["project_name"] == "JpgProject"


def test_upload_replaces_existing(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "ReplaceProject")

    buf1 = _create_test_image("PNG", (50, 50))
    client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("v1.png", buf1, "image/png")},
    )

    buf2 = _create_test_image("PNG", (80, 80))
    res = client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("v2.png", buf2, "image/png")},
    )
    assert res.status_code == 200

    get_res = client.get(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert get_res.status_code == 200


# ── GET success ──────────────────────────────────────────────────────

def test_get_thumbnail_success(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "GetProject")
    buf = _create_test_image("PNG")
    client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("img.png", buf, "image/png")},
    )

    res = client.get(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    # PNG magic bytes
    assert res.content[:4] == b"\x89PNG"


def test_get_thumbnail_not_exists(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "NoThumbProject")
    res = client.get(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert res.status_code == 404
    assert "Thumbnail not found" in res.json()["detail"]


# ── DELETE ───────────────────────────────────────────────────────────

def test_delete_thumbnail_success(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "DelProject")
    buf = _create_test_image("PNG")
    client.post(
        f"/projects/{project_id}/thumbnail",
        headers=auth_headers,
        files={"file": ("img.png", buf, "image/png")},
    )

    res = client.delete(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # GET should now 404
    get_res = client.get(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert get_res.status_code == 404


def test_delete_thumbnail_not_exists(client, auth_headers, seed_conn):
    project_id = seed_project(seed_conn, 1, "NoThumbDel")
    res = client.delete(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert res.status_code == 404
    assert "Thumbnail not found" in res.json()["detail"]


# ── Cross-user isolation ─────────────────────────────────────────────

def test_cross_user_isolation(client, auth_headers, seed_conn, consent_user_id_2):
    # User 2 creates a project with a thumbnail
    project_id = seed_project(seed_conn, consent_user_id_2, "User2Project")

    token2 = create_access_token(
        secret="test-secret-key-for-testing",
        user_id=consent_user_id_2,
        username="new-user",
        expires_minutes=60,
    )
    headers2 = {"Authorization": f"Bearer {token2}"}

    buf = _create_test_image("PNG")
    upload_res = client.post(
        f"/projects/{project_id}/thumbnail",
        headers=headers2,
        files={"file": ("img.png", buf, "image/png")},
    )
    assert upload_res.status_code == 200

    # User 1 cannot see user 2's thumbnail
    res = client.get(
        f"/projects/{project_id}/thumbnail", headers=auth_headers
    )
    assert res.status_code == 404
