import sqlite3
import pytest
from src.db.deduplication import (
    insert_project, insert_project_version, insert_version_files,
    find_existing_version_by_strict_fp, find_existing_version_by_loose_fp, get_latest_versions, get_hash_set_for_version, get_relpath_set_for_version
)

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE projects (project_key INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT)")
    conn.execute("""CREATE TABLE project_versions (
        version_key INTEGER PRIMARY KEY AUTOINCREMENT, project_key INTEGER, upload_id INTEGER,
        fingerprint_strict TEXT, fingerprint_loose TEXT)""")
    conn.execute("CREATE TABLE version_files (version_key INTEGER, relpath TEXT, file_hash TEXT, PRIMARY KEY (version_key, relpath))")
    return conn

def test_insert_project(conn):
    pk = insert_project(conn, 1, "TestProject")
    assert pk == 1
    row = conn.execute("SELECT user_id, display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
    assert row == (1, "TestProject")

def test_insert_project_version(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp_strict", "fp_loose")
    assert vk == 1
    row = conn.execute("SELECT fingerprint_strict FROM project_versions WHERE version_key = ?", (vk,)).fetchone()
    assert row[0] == "fp_strict"

def test_insert_version_files(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp", "fp")
    insert_version_files(conn, vk, [("a.py", "hash1"), ("b.py", "hash2")])
    rows = conn.execute("SELECT relpath, file_hash FROM version_files WHERE version_key = ?", (vk,)).fetchall()
    assert set(rows) == {("a.py", "hash1"), ("b.py", "hash2")}

def test_find_existing_version_by_strict_fp(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp123", "fp")
    result = find_existing_version_by_strict_fp(conn, 1, "fp123")
    assert result == (pk, vk)
    assert find_existing_version_by_strict_fp(conn, 1, "nonexistent") is None

def test_find_existing_version_by_loose_fp(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp_strict", "fp_loose123")
    result = find_existing_version_by_loose_fp(conn, 1, "fp_loose123")
    assert result == (pk, vk)
    assert find_existing_version_by_loose_fp(conn, 1, "nonexistent") is None

def test_get_latest_versions(conn):
    pk1 = insert_project(conn, 1, "Proj1")
    pk2 = insert_project(conn, 1, "Proj2")
    vk1 = insert_project_version(conn, pk1, None, "fp1", "fp1")
    vk2 = insert_project_version(conn, pk1, None, "fp2", "fp2")
    vk3 = insert_project_version(conn, pk2, None, "fp3", "fp3")
    latest = get_latest_versions(conn, 1)
    assert latest[pk1] == vk2
    assert latest[pk2] == vk3

def test_get_hash_set_for_version(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp", "fp")
    insert_version_files(conn, vk, [("a.py", "hash1"), ("b.py", "hash2")])
    hashes = get_hash_set_for_version(conn, vk)
    assert hashes == {"hash1", "hash2"}

def test_get_relpath_set_for_version(conn):
    pk = insert_project(conn, 1, "Test")
    vk = insert_project_version(conn, pk, None, "fp", "fp")
    insert_version_files(conn, vk, [("a.py", "hash1"), ("b.py", "hash2")])
    relpaths = get_relpath_set_for_version(conn, vk)
    assert relpaths == {"a.py", "b.py"}
