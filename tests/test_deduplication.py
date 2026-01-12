import pytest
from pathlib import Path
from src.utils.deduplication.helpers import should_ignore_path, jaccard_similarity
from src.utils.deduplication.fingerprints import file_content_hash, project_fingerprints
from src.utils.deduplication.rules import IGNORE_DIRS, IGNORE_FILE_SUFFIXES


# Helpers
def create_project_structure(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root

# should_ignore_path tests
def test_should_ignore_path_ignores_directories(tmp_path):
    ignored_dirs = list(IGNORE_DIRS)[:3] # Test first 3
    for dir_name in ignored_dirs:
        path = tmp_path / dir_name / "file.py"
        path.parent.mkdir()
        path.write_text("content")
        assert should_ignore_path(path) is True

def test_should_ignore_path_ignores_nested_dirs(tmp_path):
    path = tmp_path / "src" / "node_modules" / "package" / "file.js"
    path.parent.mkdir(parents=True)
    path.write_text("content")
    assert should_ignore_path(path) is True

def test_should_ignore_path_ignores_file_suffixes(tmp_path):
    ignored_suffixes = list(IGNORE_FILE_SUFFIXES)[:3]  # Test first 3
    for suffix in ignored_suffixes:
        path = tmp_path / f"file{suffix}"
        path.write_text("content")
        assert should_ignore_path(path) is True

def test_should_ignore_path_allows_valid_files(tmp_path):
    valid_paths = [
        tmp_path / "file.py",
        tmp_path / "script.js",
        tmp_path / "src" / "main.java",
        tmp_path / "docs" / "readme.txt",
    ]
    for path in valid_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content")
        assert should_ignore_path(path) is False

# jaccard_similarity tests
def test_jaccard_similarity_identical_sets():
    s = {"a", "b", "c"}
    assert jaccard_similarity(s, s) == 1.0

def test_jaccard_similarity_no_overlap():
    assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

def test_jaccard_similarity_partial_overlap():
    a = {"a", "b", "c"}
    b = {"b", "c", "d"}
    # intersection: {b, c} = 2, union: {a, b, c, d} = 4, result: 2/4 = 0.5
    assert jaccard_similarity(a, b) == 0.5

def test_jaccard_similarity_empty_sets():
    assert jaccard_similarity(set(), set()) == 1.0
    assert jaccard_similarity({"a"}, set()) == 0.0
    assert jaccard_similarity(set(), {"a"}) == 0.0

def test_jaccard_similarity_subset():
    assert jaccard_similarity({"a", "b", "c"}, {"a", "b"}) == pytest.approx(0.666, abs=0.001)

# file_content_hash tests
def test_file_content_hash_consistent(tmp_path):
    path = tmp_path / "test.py"
    path.write_text("hello\nworld", encoding="utf-8")
    h1 = file_content_hash(path)
    h2 = file_content_hash(path)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex length

def test_file_content_hash_different_content(tmp_path):
    p1 = tmp_path / "file1.py"
    p2 = tmp_path / "file2.py"
    p1.write_text("content1", encoding="utf-8")
    p2.write_text("content2", encoding="utf-8")
    assert file_content_hash(p1) != file_content_hash(p2)

def test_file_content_hash_normalizes_line_endings(tmp_path):
    p1 = tmp_path / "file1.py"
    p2 = tmp_path / "file2.py"
    p1.write_bytes(b"line1\r\nline2\r\n")  # Windows
    p2.write_bytes(b"line1\nline2\n")      # Unix
    assert file_content_hash(p1, normalize_text=True) == file_content_hash(p2, normalize_text=True)

def test_file_content_hash_no_normalization_when_disabled(tmp_path):
    p1 = tmp_path / "file1.py"
    p2 = tmp_path / "file2.py"
    p1.write_bytes(b"line1\r\nline2\r\n")
    p2.write_bytes(b"line1\nline2\n")
    # With normalize_text=False, should differ
    assert file_content_hash(p1, normalize_text=False) != file_content_hash(p2, normalize_text=False)

def test_file_content_hash_binary_no_normalization(tmp_path):
    p1 = tmp_path / "file1.bin"
    p2 = tmp_path / "file2.bin"
    p1.write_bytes(b"line1\r\nline2\r\n")
    p2.write_bytes(b"line1\nline2\n")
    # Non-text files should differ even with normalize_text=True
    assert file_content_hash(p1, normalize_text=True) != file_content_hash(p2, normalize_text=True)

# project_fingerprints tests
def test_project_fingerprints_single_file(tmp_path):
    root = create_project_structure(tmp_path / "project", {"main.py": "print('hello')"})
    fp_strict, fp_loose, entries = project_fingerprints(root)

    assert len(entries) == 1
    assert entries[0][0] == "main.py"

def test_project_fingerprints_multiple_files(tmp_path):
    root = create_project_structure(tmp_path / "project", {
        "src/main.py": "print('hello')",
        "src/utils.py": "def func(): pass",
        "README.md": "# Project"
    })
    _, _, entries = project_fingerprints(root)

    assert len(entries) == 3
    entry_paths = {e[0] for e in entries}
    assert entry_paths == {"src/main.py", "src/utils.py", "README.md"}

def test_project_fingerprints_ignores_excluded_dirs(tmp_path):
    root = create_project_structure(tmp_path, {
        "main.py": "code",
        "node_modules/pkg.js": "ignored",
        ".git/config": "ignored",
        "__pycache__/file.pyc": "ignored",
    })
    _, _, entries = project_fingerprints(root)
    
    entry_paths = {e[0] for e in entries}
    assert "main.py" in entry_paths
    assert "node_modules/pkg.js" not in entry_paths
    assert ".git/config" not in entry_paths

def test_project_fingerprints_strict_vs_loose(tmp_path):
    # Same files, different structure
    root1 = create_project_structure(tmp_path / "proj1", {"src/a.py": "content"})
    root2 = create_project_structure(tmp_path / "proj2", {"lib/a.py": "content"})
    
    fp1_strict, fp1_loose, _ = project_fingerprints(root1)
    fp2_strict, fp2_loose, _ = project_fingerprints(root2)
    
    # Strict should differ (different paths)
    assert fp1_strict != fp2_strict
    # Loose should match (same content)
    assert fp1_loose == fp2_loose

def test_project_fingerprints_empty_project(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    fp_strict, fp_loose, entries = project_fingerprints(root)
    
    assert len(entries) == 0
    # Empty project should have deterministic hash
    empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert fp_strict == empty_hash
    assert fp_loose == empty_hash

def test_project_fingerprints_deterministic_ordering(tmp_path):
    root = create_project_structure(tmp_path / "project", {
        "z.py": "z",
        "a.py": "a",
        "m.py": "m",
    })
    fp1_strict, fp1_loose, entries1 = project_fingerprints(root)
    fp2_strict, fp2_loose, entries2 = project_fingerprints(root)

    assert fp1_strict == fp2_strict
    assert fp1_loose == fp2_loose

    entries1_sorted = sorted(entries1, key=lambda x: x[0])
    assert entries1_sorted[0][0] == "a.py"
    assert entries1_sorted[1][0] == "m.py"
    assert entries1_sorted[2][0] == "z.py"