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


def fake_file(content="x", name="f.py"):
    """Creates one fake file dictionary."""
    return {"content": content, "file_name": name}


def with_patched_env(
    *,
    detectors=None,
    buckets=None,
    score_map=None,
    insert_mock=None,
):
    """
    Context manager that patches:
    - detector registry
    - bucket registry
    - score_to_level
    - insert_project_skill
    """
    detectors = detectors or {}
    buckets = buckets or []
    score_map = score_map or (lambda x: "L1") # default fake level
    insert_mock = insert_mock or Mock()

    return patch.multiple(
        "src.analysis.skills.flows.code_skill_extraction",
        CODE_DETECTOR_FUNCTIONS=detectors,
        CODE_SKILL_BUCKETS=buckets,
        score_to_level=score_map,
        insert_project_skill=insert_mock,
    )


# Tests: run_all_code_detectors
def test_run_all_code_detectors_basic():
    detectors = {
        "d1": lambda text, fname: (True, [{"file": fname, "line": 1}]),
        "d2": lambda text, fname: (False, []),
    }

    files = [fake_file("hello")]
    
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

    files = [fake_file("a"), fake_file("b")]

    with patch("src.analysis.skills.flows.code_skill_extraction.CODE_DETECTOR_FUNCTIONS", detectors):
        res = run_all_code_detectors(files)

    # 2 files = 2 hits
    assert res["d"]["hits"] == 2
    assert len(res["d"]["evidence"]) == 2


# Tests: aggregate_into_buckets
class FakeBucket:
    def __init__(self, name, detectors, total_signals=2):
        self.name = name
        self.detectors = detectors
        self.total_signals = total_signals


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
    conn = make_conn()

    # detectors produce one hit
    detectors = {
        "det": lambda t, f: (True, [{"f": f}]),
    }

    # one bucket using that detector
    fake_buckets = [FakeBucket("B", ["det"], total_signals=1)]

    insert_mock = Mock()

    with with_patched_env(detectors=detectors, buckets=fake_buckets, score_map=lambda s: "L5", insert_mock=insert_mock):
        extract_code_skills(conn, 1, "proj", "indiv", [fake_file("abc")])

    # DB write was called exactly once
    insert_mock.assert_called_once()

    args, kwargs = insert_mock.call_args
    assert kwargs["skill_name"] == "B"
    assert kwargs["level"] == "L5"
    assert kwargs["score"] == 1.0
    assert json.loads(kwargs["evidence"]) == [{"f": "f.py"}]

