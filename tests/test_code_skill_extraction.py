import sqlite3
import json
from unittest.mock import patch, Mock
from src.analysis.skills.flows.code_skill_extraction import (
    extract_code_skills,
    run_all_code_detectors,
    aggregate_into_buckets,
)


# Shared helpers
def make_conn():
    """Simple in-memory SQLite conn."""
    return sqlite3.connect(":memory:")


def make_conn_with_projects(user_id=1, display_name="proj"):
    """
    In-memory conn with minimal schema so get_project_key(conn, user_id, display_name) works.
    Used by extract_code_skills tests that pass a real conn.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO projects (user_id, display_name) VALUES (?, ?)",
        (user_id, display_name),
    )
    conn.commit()
    return conn


def fake_file(content="x", name="f.py"):
    """Creates one fake file dictionary."""
    return {"content": content, "file_name": name}


def with_patched_env(
    *,
    detectors=None,
    buckets=None,
    score_map=None,
    insert_mock=None,
    zip_name="test_zip",
):
    """
    Context manager that patches:
    - detector registry
    - bucket registry
    - score_to_level
    - insert_project_skill
    - _get_zip_name (returns zip_name)
    - _load_file_contents (returns files as-is with content already set)
    """
    detectors = detectors or {}
    buckets = buckets or []
    score_map = score_map or (lambda x: "L1") # default fake level
    insert_mock = insert_mock or Mock()

    # Mock _get_zip_name to return the zip_name
    # Mock _load_file_contents to just return files as-is (test files already have content)
    return patch.multiple(
        "src.analysis.skills.flows.code_skill_extraction",
        CODE_DETECTOR_FUNCTIONS=detectors,
        CODE_SKILL_BUCKETS=buckets,
        score_to_level=score_map,
        insert_project_skill=insert_mock,
        _get_zip_name=Mock(return_value=zip_name),
        _load_file_contents=Mock(side_effect=lambda files, zn: files),
    )


# Tests: run_all_code_detectors
def test_run_all_code_detectors_basic():
    detectors = {
        "d1": lambda text, fname: (True, [{"file": fname, "line": 1}]),
        "d2": lambda text, fname: (False, []),
    }

    files = [fake_file("line1\nline2\nline3")]
    
    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_DETECTOR_FUNCTIONS", detectors):
        res = run_all_code_detectors(files)

    assert res["d1"]["hits"] == 1
    assert res["d1"]["evidence"]
    assert res["d2"]["hits"] == 0
    assert res["d2"]["evidence"] == []


def test_run_all_code_detectors_multiple_files_and_hits():
    detectors = {
        "d": lambda text, fname: (True, [{"file": fname, "line": 1}]),
    }

    files = [fake_file("a\nb\nc"), fake_file("x\ny\nz")]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_DETECTOR_FUNCTIONS", detectors):
        res = run_all_code_detectors(files)

    # 2 files = 2 hits
    assert res["d"]["hits"] == 2
    assert len(res["d"]["evidence"]) == 2


# Tests: aggregate_into_buckets
class FakeBucket:
    def __init__(self, name, detectors, total_signals=2, weights=None):
        self.name = name
        self.detectors = detectors
        self.total_signals = total_signals
        self.weights = weights if weights is not None else {}


def test_aggregate_buckets_basic():
    detector_results = {
        "d1": {"hits": 1, "evidence": [{"e": 1}]},
        "d2": {"hits": 0, "evidence": []},
    }

    fake_buckets = [
        FakeBucket("bucket1", ["d1", "d2"]),
    ]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_SKILL_BUCKETS", fake_buckets), \
         patch("src.analysis.skills.flows.code_skill_extraction.score_to_level", return_value="L3"):
        
        res = aggregate_into_buckets(detector_results)

    assert "bucket1" in res
    assert res["bucket1"]["score"] == 0.5
    assert res["bucket1"]["level"] == "L3"
    assert res["bucket1"]["evidence"] == [{"e": 1}]


def test_aggregate_buckets_all_zero():
    detector_results = {"d": {"hits": 0, "evidence": []}}
    fake_buckets = [FakeBucket("b", ["d"])]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_SKILL_BUCKETS", fake_buckets), \
         patch("src.analysis.skills.flows.code_skill_extraction.score_to_level", return_value="L0"):

        res = aggregate_into_buckets(detector_results)

    assert res["b"]["score"] == 0
    assert res["b"]["level"] == "L0"
    assert res["b"]["evidence"] == []


# Tests: extract_code_skills

def test_extract_code_skills_happy_path():
    # Minimal schema so get_project_key(conn, 1, "proj") succeeds (no such table: projects otherwise)
    conn = make_conn_with_projects(user_id=1, display_name="proj")

    # detectors produce one hit
    detectors = {
        "det": lambda t, f: (True, [{"f": f}]),
    }

    # one bucket using that detector
    fake_buckets = [FakeBucket("B", ["det"], total_signals=1)]

    insert_mock = Mock()

    with with_patched_env(detectors=detectors, buckets=fake_buckets, score_map=lambda s: "L5", insert_mock=insert_mock):
        extract_code_skills(conn, 1, "proj", "indiv", [fake_file("line1\nline2\nline3")])

    # DB write was called exactly once
    insert_mock.assert_called_once()

    args, kwargs = insert_mock.call_args
    assert kwargs["skill_name"] == "B"
    assert kwargs["level"] == "L5"
    assert kwargs["score"] == 1.0
    assert json.loads(kwargs["evidence"]) == [{"f": "f.py"}]


# Tests: weighted scoring (negative weights)

def test_aggregate_buckets_with_negative_weight():
    """Test that negative weights reduce the score."""
    detector_results = {
        "good_detector": {"hits": 1, "evidence": [{"e": 1}]},
        "bad_detector": {"hits": 1, "evidence": [{"e": 2}]},
    }

    fake_buckets = [
        FakeBucket(
            "quality_bucket",
            ["good_detector", "bad_detector"],
            total_signals=2,
            weights={
                "good_detector": 1,   # positive
                "bad_detector": -1,   # negative
            }
        ),
    ]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_SKILL_BUCKETS", fake_buckets), \
         patch("src.analysis.skills.flows.code_skill_extraction.score_to_level", return_value="L0"):

        res = aggregate_into_buckets(detector_results)

    # weighted_signals = 1 + (-1) = 0
    # max_score = 1 (only good_detector is positive)
    # score = 0/1 = 0.0
    assert res["quality_bucket"]["score"] == 0.0
    assert res["quality_bucket"]["level"] == "L0"


def test_aggregate_buckets_negative_clamped_to_zero():
    """Test that negative scores are clamped to 0."""
    detector_results = {
        "bad1": {"hits": 1, "evidence": [{"e": 1}]},
        "bad2": {"hits": 1, "evidence": [{"e": 2}]},
        "good": {"hits": 0, "evidence": []},
    }

    fake_buckets = [
        FakeBucket(
            "quality",
            ["good", "bad1", "bad2"],
            total_signals=3,
            weights={
                "good": 1,
                "bad1": -1,
                "bad2": -1,
            }
        ),
    ]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_SKILL_BUCKETS", fake_buckets), \
         patch("src.analysis.skills.flows.code_skill_extraction.score_to_level", return_value="L0"):

        res = aggregate_into_buckets(detector_results)

    # weighted_signals = 0 + (-1) + (-1) = -2, clamped to 0
    # max_score = 1 (only good is positive)
    # score = 0/1 = 0.0
    assert res["quality"]["score"] == 0.0
    assert res["quality"]["level"] == "L0"