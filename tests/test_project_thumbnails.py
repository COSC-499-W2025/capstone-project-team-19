import sqlite3
import pytest

from src.db.project_thumbnails import (
    upsert_project_thumbnail,
    get_project_thumbnail_path,
    delete_project_thumbnail,
    list_thumbnail_projects,
)


@pytest.fixture()
def mem_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE project_thumbnails (
            thumbnail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            image_path   TEXT NOT NULL,
            added_at     TEXT NOT NULL,
            updated_at   TEXT NOT NULL,
            UNIQUE(user_id, project_name)
        )
        """
    )
    conn.commit()
    return conn


def test_project_thumbnail_crud(mem_conn):
    user_id = 1
    project_name = "paper"

    # Initially none
    assert get_project_thumbnail_path(mem_conn, user_id, project_name) is None
    assert list_thumbnail_projects(mem_conn, user_id) == []

    # Add
    upsert_project_thumbnail(mem_conn, user_id, project_name, "./images/u1_paper.png")
    assert get_project_thumbnail_path(mem_conn, user_id, project_name) == "./images/u1_paper.png"
    assert list_thumbnail_projects(mem_conn, user_id) == ["paper"]

    # Update (upsert replaces path)
    upsert_project_thumbnail(mem_conn, user_id, project_name, "./images/u1_paper_v2.png")
    assert get_project_thumbnail_path(mem_conn, user_id, project_name) == "./images/u1_paper_v2.png"
    assert list_thumbnail_projects(mem_conn, user_id) == ["paper"]

    # Delete
    assert delete_project_thumbnail(mem_conn, user_id, project_name) is True
    assert get_project_thumbnail_path(mem_conn, user_id, project_name) is None
    assert list_thumbnail_projects(mem_conn, user_id) == []

    # Delete again -> false
    assert delete_project_thumbnail(mem_conn, user_id, project_name) is False
