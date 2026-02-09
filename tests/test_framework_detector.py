import os
import sqlite3
import shutil
from pathlib import Path

import pytest

#from src.framework_detector import detect_frameworks as fd
from src.utils import framework_detector as fd


@pytest.fixture
def conn():
    """In-memory sqlite DB with minimal projects + config_files (project_key) for detector."""
    c = sqlite3.connect(":memory:")
    cur = c.cursor()
    cur.execute(
        """
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE config_files (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_key INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT
        )
        """
    )
    c.commit()
    yield c
    c.close()


def _ensure_project(conn, user_id, project_name):
    """Insert project if missing; return project_key."""
    row = conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (user_id, project_name),
    ).fetchone()
    if row:
        return row[0]
    conn.execute(
        "INSERT INTO projects (user_id, display_name) VALUES (?, ?)",
        (user_id, project_name),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def _repo_zip_base(zip_name):
    """Return the expected base path used by framework_detector for a given zip_name."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(fd.__file__)))
    base = os.path.join(repo_root, "analysis", "zip_data", zip_name)
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

def _test_framework_detection(conn, zip_name, file_path, file_content, project_name, user_id, expected_frameworks):
    """Helper function to reduce test boilerplate."""
    try:
        _make_zip_data_file(zip_name, file_path, file_content)
        project_key = _ensure_project(conn, user_id, project_name)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (user_id, project_key, file_name, file_path) VALUES (?, ?, ?, ?)",
            (user_id, project_key, os.path.basename(file_path), file_path),
        )
        conn.commit()

        frameworks = fd.detect_frameworks(conn, project_name, user_id, zip_name + ".zip")

        for fw in expected_frameworks:
            assert fw in frameworks, f"Expected {fw} but got {frameworks}"

        return frameworks
    finally:
        _cleanup_zip_data(zip_name)

# Test cases
def test_missing_config_file_is_skipped(conn):
    """Handles cases where a config file listed in DB is missing on disk."""
    zip_name = "sample_zip_missing"
    try:
        # Do NOT create the actual file on disk, only add DB reference
        project_key = _ensure_project(conn, 2, "projB")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (user_id, project_key, file_name, file_path) VALUES (?, ?, ?, ?)",
            (2, project_key, "does_not_exist.cfg", "does_not_exist.cfg"),
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

        project_key = _ensure_project(conn, 4, "projD")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO config_files (user_id, project_key, file_name, file_path) VALUES (?, ?, ?, ?)",
            (4, project_key, "not_a_file.txt", "not_a_file.txt"),
        )
        conn.commit()

        # Should not raise, and should simply return empty set
        frameworks = fd.detect_frameworks(conn, "projD", 4, zip_name + ".zip")
        assert frameworks == set()
    finally:
        _cleanup_zip_data(zip_name)

def test_detects_single_framework(conn):
    """Detects Flask from requirements.txt"""
    frameworks = _test_framework_detection(
        conn, "flask_version_zip", "requirements.txt", "Flask==2.2.5\n",
        "basicProj", 10, ["Flask"]
    )
    assert "Django" not in frameworks

def test_detects_multiple_frameworks_in_one_project(conn):
    """Detects both Flask and Django from requirements.txt"""
    _test_framework_detection(
        conn, "multi_frameworks_zip", "requirements.txt", "Flask==2.2.5\nDjango>=3.2\n",
        "multiProj", 11, ["Flask", "Django"]
    )

def test_no_frameworks_present_returns_empty(conn):
    """Returns empty set when no known frameworks are detected."""
    frameworks = _test_framework_detection(
        conn, "no_frameworks_zip", "requirements.txt", "requests==2.31.0\nnumpy==1.24.0\n",
        "emptyProj", 12, []
    )
    assert frameworks == set()

def test_detects_python_web_frameworks(conn):
    """Detects multiple Python web frameworks from requirements.txt"""
    _test_framework_detection(
        conn, "python_web_zip", "requirements.txt", "FastAPI==0.100.0\nstreamlit==1.24.0\ntornado>=6.0\n",
        "pyWebProj", 20, ["FastAPI", "Streamlit", "Tornado"]
    )

def test_detects_javascript_frameworks_from_package_json(conn):
    """Detects JavaScript frameworks from package.json"""
    _test_framework_detection(
        conn, "js_frameworks_zip", "package.json",
        '{"dependencies": {"react": "^18.2.0", "next": "^13.0.0", "axios": "^1.4.0"}, "devDependencies": {"jest": "^29.0.0", "cypress": "^12.0.0"}}',
        "jsProj", 21, ["React", "Next.js", "Axios", "Jest", "Cypress"]
    )

def test_detects_orm_and_state_management(conn):
    """Detects ORM and state management libraries"""
    _test_framework_detection(
        conn, "orm_state_zip", "package.json",
        '{"dependencies": {"prisma": "^5.0.0", "@prisma/client": "^5.0.0", "redux": "^4.2.0", "zustand": "^4.3.0"}}',
        "ormProj", 22, ["Prisma", "Redux", "Zustand"]
    )

def test_detects_mobile_frameworks(conn):
    """Detects mobile frameworks"""
    _test_framework_detection(
        conn, "mobile_zip", "package.json",
        '{"dependencies": {"react-native": "^0.72.0", "expo": "^49.0.0"}}',
        "mobileProj", 23, ["React Native", "Expo"]
    )

def test_detects_css_frameworks(conn):
    """Detects CSS frameworks and preprocessors"""
    _test_framework_detection(
        conn, "css_zip", "package.json",
        '{"dependencies": {"@mui/material": "^5.14.0", "styled-components": "^6.0.0"}, "devDependencies": {"sass": "^1.64.0"}}',
        "cssProj", 24, ["Material-UI", "Styled Components", "Sass"]
    )

def test_detects_build_tools(conn):
    """Detects build tools and bundlers"""
    _test_framework_detection(
        conn, "build_tools_zip", "package.json",
        '{"devDependencies": {"vite": "^4.4.0", "webpack": "^5.88.0", "esbuild": "^0.18.0"}}',
        "buildProj", 25, ["Vite", "Webpack", "esbuild"]
    )
