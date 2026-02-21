import base64
import sqlite3
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_db, get_current_user_id
from src.api.routes.activity_heatmap import router as activity_heatmap_router


# 1x1 PNG (valid)
SAMPLE_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/a7lYQAAAABJRU5ErkJggg=="
)


def override_get_db():
    conn = sqlite3.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


def override_get_current_user_id():
    return 1


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(activity_heatmap_router)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    return TestClient(app)


def test_get_activity_heatmap_png_success(client, tmp_path):
    png_path = tmp_path / "heatmap.png"
    png_path.write_bytes(SAMPLE_PNG_BYTES)

    # Patch the symbol used by the router module (important!)
    with patch(
        "src.api.routes.activity_heatmap.get_activity_heatmap_png_path",
        return_value=str(png_path),
    ):
        resp = client.get("/projects/MyProject/activity-heatmap.png?mode=diff&normalize=true")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_get_activity_heatmap_png_project_not_found(client):
    with patch(
        "src.api.routes.activity_heatmap.get_activity_heatmap_png_path",
        side_effect=ValueError("Project not found"),
    ):
        resp = client.get("/projects/Nope/activity-heatmap.png?mode=diff")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"