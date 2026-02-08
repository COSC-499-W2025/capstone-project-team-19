# tests/api/conftest.py
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone

import src.db as db
from src.api.main import app
from src.api.dependencies import get_db, get_jwt_secret
from src.api.auth.security import hash_password, create_access_token

TEST_JWT_SECRET = "test-secret-key-for-testing"

@pytest.fixture(autouse=True)
def shared_db(tmp_path, monkeypatch):
    """
    API-safe DB setup:
    - uses an on-disk temp DB (shared by path)
    - DOES NOT share a single sqlite Connection across threads
    """
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)

    # initialize schema once
    conn = sqlite3.connect(db_path, check_same_thread=False)
    db.init_schema(conn)
    conn.close()

    yield  # test runs

    monkeypatch.delenv("APP_DB_PATH", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    TestClient that overrides dependencies so each request gets its own connection.
    """
    db_path = Path(os.environ["APP_DB_PATH"])

    def override_get_db():
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        db.init_schema(conn)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_jwt_secret] = lambda: TEST_JWT_SECRET

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def seed_conn():
    """Convenience: a connection you can use to seed test data."""
    db_path = os.environ["APP_DB_PATH"]
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db.init_schema(conn)
    yield conn
    conn.close()

@pytest.fixture
def consent_user_id_1(seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()
    return 1

@pytest.fixture
def consent_user_id_2(seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (2, 'new-user', NULL)"
    )
    seed_conn.commit()
    return 2

@pytest.fixture
def auth_headers(consent_user_id_1):
    token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=consent_user_id_1,
        username="test-user",
        expires_minutes=60,
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_nonexistent_user():
    """Create a token for a user ID that doesn't exist in the database."""
    token = create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=999999,
        username="nonexistent",
        expires_minutes=60,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def git_repo_zip(tmp_path):
    if not shutil.which("git"):
        pytest.skip("git not installed")

    root_name = "test"
    project_name = "ProjectA"
    root_dir = tmp_path / root_name
    project_dir = root_dir / project_name
    project_dir.mkdir(parents=True)

    subprocess.check_call(["git", "init"], cwd=project_dir)

    file1 = project_dir / "file1.txt"
    file1.write_text("hello", encoding="utf-8")
    subprocess.check_call(["git", "add", "file1.txt"], cwd=project_dir)
    env1 = os.environ.copy()
    env1.update(
        {
            "GIT_AUTHOR_NAME": "Alice",
            "GIT_AUTHOR_EMAIL": "alice@example.com",
            "GIT_COMMITTER_NAME": "Alice",
            "GIT_COMMITTER_EMAIL": "alice@example.com",
        }
    )
    subprocess.check_call(["git", "commit", "-m", "commit 1"], cwd=project_dir, env=env1)

    file2 = project_dir / "file2.txt"
    file2.write_text("hi", encoding="utf-8")
    subprocess.check_call(["git", "add", "file2.txt"], cwd=project_dir)
    env2 = os.environ.copy()
    env2.update(
        {
            "GIT_AUTHOR_NAME": "Bob",
            "GIT_AUTHOR_EMAIL": "bob@example.com",
            "GIT_COMMITTER_NAME": "Bob",
            "GIT_COMMITTER_EMAIL": "bob@example.com",
        }
    )
    subprocess.check_call(["git", "commit", "-m", "commit 2"], cwd=project_dir, env=env2)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path in root_dir.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(root_dir.parent))
    return buf.getvalue()


@pytest.fixture
def uploaded_git_zip(client, auth_headers, git_repo_zip):
    res = client.post(
        "/projects/upload",
        headers=auth_headers,
        files={"file": ("test.zip", git_repo_zip, "application/zip")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    return body["data"]


@pytest.fixture
def insert_classification(seed_conn):
    def _insert(
        *,
        user_id: int,
        upload: dict,
        project_name: str,
        classification: str,
        project_type: str,
    ) -> int:
        cur = seed_conn.execute(
            """
            INSERT INTO projects(user_id, display_name, classification, project_type)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, project_name, classification, project_type),
        )
        project_key = cur.lastrowid

        fingerprint = f"test-{user_id}-{project_name}-{upload.get('upload_id')}"
        seed_conn.execute(
            """
            INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                project_key,
                upload.get("upload_id"),
                fingerprint,
                fingerprint,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        seed_conn.commit()
        return project_key

    return _insert
