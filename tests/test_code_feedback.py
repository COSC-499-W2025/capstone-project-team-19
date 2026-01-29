import json
import sqlite3
from pathlib import Path

import pytest

# Import the module under test
from src.analysis.skills.flows import code_skill_extraction as cse


@pytest.fixture()
def conn(tmp_path: Path):
    # In-memory DB + load the REAL schema
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    schema_path = Path("src/db/schema/tables.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))

    # Minimal rows needed by extract_code_skills()
    db.execute("INSERT INTO users (username) VALUES (?)", ("testuser",))
    user_id = db.execute("SELECT user_id FROM users WHERE username=?", ("testuser",)).fetchone()[0]

    db.execute(
        """
        INSERT INTO project_classifications
            (user_id, zip_path, zip_name, project_name, classification, project_type, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, "/tmp/fake.zip", "zip_test", "proj", "individual", "code"),
    )
    db.commit()

    return db


@pytest.fixture()
def user_id(conn):
    return conn.execute("SELECT user_id FROM users WHERE username=?", ("testuser",)).fetchone()[0]


@pytest.fixture()
def patch_detectors_and_buckets(monkeypatch):
    """
    Make tests deterministic:
      - Define only the 3 detectors we care about
      - Define a single bucket that depends exactly on them
    """

    def detect_hash_maps(lines, file_name):
        hit = any("{" in line and ":" in line for line in lines) or any("dict(" in line for line in lines)
        return (hit, [{"file": file_name, "line": 1}] if hit else [])

    def detect_serialization(lines, file_name):
        hit = any("json.dumps" in line or "JSON.stringify" in line for line in lines)
        return (hit, [{"file": file_name, "line": 1}] if hit else [])

    def detect_caching(lines, file_name):
        hit = any("@lru_cache" in line or "Redis(" in line or "cache.get" in line for line in lines)
        return (hit, [{"file": file_name, "line": 1}] if hit else [])

    monkeypatch.setattr(
        cse,
        "CODE_DETECTOR_FUNCTIONS",
        {
            "detect_hash_maps": detect_hash_maps,
            "detect_serialization": detect_serialization,
            "detect_caching": detect_caching,
        },
        raising=True,
    )

    class _Bucket:
        def __init__(self, name, detectors, weights):
            self.name = name
            self.detectors = detectors
            self.weights = weights
            self.total_signals = len(detectors)

    monkeypatch.setattr(
        cse,
        "CODE_SKILL_BUCKETS",
        [
            _Bucket(
                name="backend",
                detectors=["detect_hash_maps", "detect_serialization", "detect_caching"],
                weights={"detect_hash_maps": 1, "detect_serialization": 1, "detect_caching": 1},
            )
        ],
        raising=True,
    )


def _fetch_feedback(conn, user_id, project_name):
    rows = conn.execute(
        """
        SELECT skill_name, criterion_key, criterion_label, expected, observed_json, suggestion
        FROM project_feedback
        WHERE user_id=? AND project_name=?
        ORDER BY skill_name, criterion_key
        """,
        (user_id, project_name),
    ).fetchall()
    return [dict(r) for r in rows]


def test_expected_feedback_when_no_code_file(conn, user_id, monkeypatch):
    # Make code_extensions only recognize .py so .txt/.md are not code
    monkeypatch.setattr(cse, "code_extensions", lambda: {".py"}, raising=True)

    # Ensure we never load content (should exit earlier anyway)
    monkeypatch.setattr(cse, "_load_file_contents", lambda files, zip_name: [], raising=True)

    files = [
        {"file_name": "notes.txt", "file_path": "notes.txt"},
        {"file_name": "readme.md", "file_path": "readme.md"},
    ]

    cse.extract_code_skills(conn, user_id, "proj", "individual", files)

    fb = _fetch_feedback(conn, user_id, "proj")
    assert len(fb) == 1
    assert fb[0]["criterion_key"] == "code.no_code_files"
    assert fb[0]["skill_name"] == "general"


def test_expected_feedback_when_unmet_criteria_for_caching_serialization_hashmaps(
    conn, user_id, monkeypatch, patch_detectors_and_buckets
):
    monkeypatch.setattr(cse, "code_extensions", lambda: {".py"}, raising=True)

    # Feed one Python file with NONE of the patterns
    monkeypatch.setattr(
        cse,
        "_load_file_contents",
        lambda files, zip_name: [
            {"file_name": "a.py", "file_path": "a.py", "content": "def f():\n    return 1\n"}
        ],
        raising=True,
    )

    files = [{"file_name": "a.py", "file_path": "a.py"}]
    cse.extract_code_skills(conn, user_id, "proj", "individual", files)

    fb = _fetch_feedback(conn, user_id, "proj")

    # Should emit exactly 3 unmet criteria (caching, serialization, hash_maps) for bucket "backend"
    keys = {r["criterion_key"] for r in fb}
    assert keys == {
        "backend.detect_hash_maps",
        "backend.detect_serialization",
        "backend.detect_caching",
    }


def test_expected_feedback_when_project_score_is_100(
    conn, user_id, monkeypatch, patch_detectors_and_buckets
):
    monkeypatch.setattr(cse, "code_extensions", lambda: {".py"}, raising=True)

    # Content hits all 3 detectors -> bucket score 1.0 -> no missing criteria -> no feedback
    code = "\n".join(
        [
            "import json",
            "from functools import lru_cache",
            "@lru_cache(maxsize=128)",
            "def f(x):",
            "    d = {'a': 1}",
            "    return json.dumps(d)",
        ]
    )

    monkeypatch.setattr(
        cse,
        "_load_file_contents",
        lambda files, zip_name: [{"file_name": "a.py", "file_path": "a.py", "content": code}],
        raising=True,
    )

    files = [{"file_name": "a.py", "file_path": "a.py"}]
    cse.extract_code_skills(conn, user_id, "proj", "individual", files)

    fb = _fetch_feedback(conn, user_id, "proj")
    assert fb == []