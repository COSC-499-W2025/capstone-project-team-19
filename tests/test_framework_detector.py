import os
import sqlite3
import shutil
from pathlib import Path

import pytest

#from src.framework_detector import detect_frameworks as fd
from src import framework_detector as fd


@pytest.fixture
def conn():
    """In-memory sqlite DB with minimal config_files table used by detector."""
    c = sqlite3.connect(":memory:")
    cur = c.cursor()
    cur.execute(
        """
        CREATE TABLE config_files (
            id INTEGER PRIMARY KEY,
            file_name TEXT,
            file_path TEXT,
            user_id INTEGER,
            project_name TEXT
        )
        """
    )
    c.commit()
    yield c
    c.close()


def _repo_zip_base(zip_name):
    """Return the expected base path used by framework_detector for a given zip_name."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(fd.__file__)))
    base = os.path.join(repo_root, "zip_data", zip_name)
    return repo_root, base


def _make_zip_data_file(zip_name, rel_path, content):
    repo_root, base = _repo_zip_base(zip_name)
    os.makedirs(os.path.dirname(os.path.join(base, rel_path)), exist_ok=True)
    full = os.path.join(base, rel_path)
    Path(full).write_text(content, encoding="utf-8")
    return full


def _cleanup_zip_data(zip_name):
    repo_root, base = _repo_zip_base(zip_name)
    zip_data_dir = os.path.join(repo_root, "zip_data")
    if os.path.exists(zip_data_dir):
        # remove only the specific zip_name folder if present
        target = os.path.join(zip_data_dir, zip_name)
        if os.path.exists(target):
            shutil.rmtree(target)
        # if zip_data became empty, optionally remove it (safe guard)
        try:
            if os.path.exists(zip_data_dir) and not os.listdir(zip_data_dir):
                shutil.rmtree(zip_data_dir)
        except OSError:
            pass

# Test cases
def test_missing_config_file_is_skipped(conn):
    """Handles cases where a config file listed in DB is missing on disk."""
    zip_name = "sample_zip_missing"
    try:
        # Do NOT create the actual file on disk, only add DB reference
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (file_name, file_path, user_id, project_name) VALUES (?, ?, ?, ?)",
            ("does_not_exist.cfg", "does_not_exist.cfg", 2, "projB"),
        )
        conn.commit()

        frameworks = fd.detect_frameworks(conn, "projB", 2, zip_name + ".zip")
        assert frameworks == set()
    finally:
        _cleanup_zip_data(zip_name)

def test_unreadable_config_entry_is_handled_gracefully(conn):
    """Handles cases where a config file cannot be opened/read."""
    zip_name = "bad_entry_zip"
    try:
        # create a directory where a file is expected to force an open() error
        repo_root, base = _repo_zip_base(zip_name)
        os.makedirs(os.path.join(base), exist_ok=True)
        problematic = os.path.join(base, "not_a_file.txt")
        os.makedirs(problematic, exist_ok=True)  # create directory instead of file

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (file_name, file_path, user_id, project_name) VALUES (?, ?, ?, ?)",
            ("not_a_file.txt", "not_a_file.txt", 4, "projD"),
        )
        conn.commit()

        # Should not raise, and should simply return empty set
        frameworks = fd.detect_frameworks(conn, "projD", 4, zip_name + ".zip")
        assert frameworks == set()
    finally:
        _cleanup_zip_data(zip_name)

def test_detects_single_framework(conn):
    """Detects Flask from requirements.txt"""
    zip_name = "flask_version_zip"
    try:
        _make_zip_data_file(zip_name, "requirements.txt", "Flask==2.2.5\n")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (file_name, file_path, user_id, project_name) VALUES (?, ?, ?, ?)",
            ("requirements.txt", "requirements.txt", 10, "basicProj"),
        )
        conn.commit()

        frameworks = fd.detect_frameworks(conn, "basicProj", 10, zip_name + ".zip")
        assert "Flask" in frameworks
        # ensure no unrelated frameworks detected
        assert "Django" not in frameworks
    finally:
        _cleanup_zip_data(zip_name)

def test_detects_multiple_frameworks_in_one_project(conn):
    """Detects both Flask and Django from requirements.txt"""
    zip_name = "multi_frameworks_zip"
    try:
        # requirements containing both Flask and Django
        _make_zip_data_file(zip_name, "requirements.txt", "Flask==2.2.5\nDjango>=3.2\n")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (file_name, file_path, user_id, project_name) VALUES (?, ?, ?, ?)",
            ("requirements.txt", "requirements.txt", 11, "multiProj"),
        )
        conn.commit()

        frameworks = fd.detect_frameworks(conn, "multiProj", 11, zip_name + ".zip")
        assert "Flask" in frameworks
        assert "Django" in frameworks
    finally:
        _cleanup_zip_data(zip_name)

def test_no_frameworks_present_returns_empty(conn):
    """Returns empty set when no known frameworks are detected."""
    zip_name = "no_frameworks_zip"
    try:
        # requirements with unrelated packages
        _make_zip_data_file(zip_name, "requirements.txt", "requests==2.31.0\nnumpy==1.24.0\n")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (file_name, file_path, user_id, project_name) VALUES (?, ?, ?, ?)",
            ("requirements.txt", "requirements.txt", 12, "emptyProj"),
        )
        conn.commit()

        frameworks = fd.detect_frameworks(conn, "emptyProj", 12, zip_name + ".zip")
        assert frameworks == set()
    finally:
        _cleanup_zip_data(zip_name)