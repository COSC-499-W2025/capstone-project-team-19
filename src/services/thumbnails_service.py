from __future__ import annotations

import os
import tempfile
from pathlib import Path
from sqlite3 import Connection

from fastapi import UploadFile
from PIL import UnidentifiedImageError

from src.db.project_summaries import get_project_summary_by_id
from src.db.project_thumbnails import (
    delete_project_thumbnail,
    get_project_thumbnail_path,
    upsert_project_thumbnail,
)
from src.utils.image_utils import save_standardized_thumbnail, validate_image_path

IMAGES_DIR = Path("./images")


def upload_thumbnail(
    conn: Connection,
    user_id: int,
    project_id: int,
    file: UploadFile,
) -> dict | None:
    """Upload or replace a project thumbnail.

    Returns result dict on success, None if project not found.
    Raises ValueError on invalid image.
    """
    project = get_project_summary_by_id(conn, user_id, project_id)
    if project is None:
        return None

    project_key = project["project_key"]
    project_name = project["project_name"]

    suffix = Path(file.filename or "upload.png").suffix or ".png"
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(file.file.read())

        try:
            validate_image_path(tmp_path)
        except UnidentifiedImageError as exc:
            raise ValueError(str(exc)) from exc
        dst = save_standardized_thumbnail(
            Path(tmp_path), IMAGES_DIR, user_id, project_name
        )
        upsert_project_thumbnail(conn, user_id, project_key, str(dst))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {
        "project_id": project_id,
        "project_name": project_name,
        "message": "Thumbnail uploaded successfully",
    }


def get_thumbnail(
    conn: Connection,
    user_id: int,
    project_id: int,
) -> str | None | bool:
    """Return the file path for a project's thumbnail.

    Returns None if project not found, False if no thumbnail, or the path string.
    """
    project = get_project_summary_by_id(conn, user_id, project_id)
    if project is None:
        return None

    path = get_project_thumbnail_path(conn, user_id, project["project_key"])
    if path is None or not Path(path).is_file():
        return False

    return path


def remove_thumbnail(
    conn: Connection,
    user_id: int,
    project_id: int,
) -> bool | None:
    """Remove a project's thumbnail.

    Returns None if project not found, False if no thumbnail, True if deleted.
    """
    project = get_project_summary_by_id(conn, user_id, project_id)
    if project is None:
        return None

    project_key = project["project_key"]
    image_path = get_project_thumbnail_path(conn, user_id, project_key)
    if image_path is None:
        return False

    delete_project_thumbnail(conn, user_id, project_key)

    p = Path(image_path)
    if p.exists() and p.parent.resolve() == IMAGES_DIR.resolve():
        p.unlink(missing_ok=True)

    return True
