import pytest
from pathlib import Path
from src.utils.deduplication.register_project import register_project
from src.utils.deduplication.fingerprints import project_fingerprints

def create_project(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content)
    return root

@pytest.fixture
def conn():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE projects (project_key INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT)")
    conn.execute("CREATE TABLE project_versions (version_key INTEGER PRIMARY KEY AUTOINCREMENT, project_key INTEGER, upload_id INTEGER, fingerprint_strict TEXT, fingerprint_loose TEXT)")
    conn.execute("CREATE TABLE version_files (version_key INTEGER, relpath TEXT, file_hash TEXT, PRIMARY KEY (version_key, relpath))")
    return conn

def test_register_project_new_project(conn, tmp_path):
    proj_dir = create_project(tmp_path / "proj", {"a.py": "code"})
    result = register_project(conn, 1, "Test", str(proj_dir))
    assert result["kind"] == "new_project"
    assert "project_key" in result
    assert "version_key" in result

def test_register_project_duplicate(conn, tmp_path):
    proj_dir = create_project(tmp_path / "proj", {"a.py": "code"})
    result1 = register_project(conn, 1, "Test", str(proj_dir))
    result2 = register_project(conn, 1, "Test2", str(proj_dir))
    assert result2["kind"] == "duplicate"
    assert result2["project_key"] == result1["project_key"]
