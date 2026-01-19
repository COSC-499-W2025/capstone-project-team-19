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

def test_register_project_duplicate_exact_structure(conn, tmp_path):
    """Exact duplicate with same files, same paths → exact duplicate."""
    proj_dir1 = create_project(tmp_path / "proj1", {"src/a.py": "content", "src/b.py": "data"})
    proj_dir2 = create_project(tmp_path / "proj2", {"src/a.py": "content", "src/b.py": "data"})
    
    result1 = register_project(conn, 1, "Test", str(proj_dir1))
    result2 = register_project(conn, 1, "Test2", str(proj_dir2))
    
    # Should be exact duplicate because content AND structure match
    assert result2["kind"] == "duplicate"
    assert result2["project_key"] == result1["project_key"]

def test_register_project_duplicate_renamed_files(conn, tmp_path):
    """Same content but all files renamed should ask user (not exact duplicate)."""
    proj_dir1 = create_project(tmp_path / "proj1", {"a.py": "content", "b.py": "data"})
    proj_dir2 = create_project(tmp_path / "proj2", {"x.py": "content", "y.py": "data"})
    
    result1 = register_project(conn, 1, "Test", str(proj_dir1))
    result2 = register_project(conn, 1, "Test2", str(proj_dir2))
    
    # Should ask user because content matches but structure differs
    assert result2["kind"] == "ask"
    assert result2["best_match_project_key"] == result1["project_key"]
    assert result2["similarity"] == 1.0  # Content is 100% identical