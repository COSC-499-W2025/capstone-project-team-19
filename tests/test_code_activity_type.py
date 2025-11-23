# Tests for the code activity type module (formatter + summary logic).

import textwrap
import pytest
from src.analysis.activity_type.code.types import (
    ActivityType,
    Scope,
    ActivitySummary,
)
from src.analysis.activity_type.code.formatter import (
    format_activity_summary,
    _shorten_top_file,  # internal but OK to test
)
import src.analysis.activity_type.code.summary as summary_mod


# ---------- _shorten_top_file tests ----------

def test_shorten_top_file_strips_prefix_before_project_name():
    """
    Ensure _shorten_top_file removes junk dirs before the project name.
    """
    path = "real_test/COSC-304-Final-Project/node_modules/pkg/file.js"
    shortened = _shorten_top_file(path, project_name="COSC-304-Final-Project")
    assert shortened == "COSC-304-Final-Project/node_modules/pkg/file.js"


def test_shorten_top_file_falls_back_to_node_modules_when_project_missing():
    """
    If project name is not in the path, fall back to 'node_modules/' marker.
    """
    path = "some/other/root/node_modules/pkg/file.js"
    shortened = _shorten_top_file(path, project_name="NotInPath")
    assert shortened == "node_modules/pkg/file.js"


def test_shorten_top_file_returns_original_if_no_project_and_no_marker():
    """
    If neither project name nor 'node_modules/' is present, path should be unchanged.
    """
    path = "src/app/main.py"
    shortened = _shorten_top_file(path, project_name="COSC-304-Final-Project")
    assert shortened == path


# ---------- format_activity_summary tests ----------

def test_format_activity_summary_no_header_and_has_percentages():
    """
    format_activity_summary should:
      - print 'Activity summary (by files/PRs):'
      - print lines with 'count/total -> XX.XX%' and shortened top file paths
    """
    per_activity = {
        ActivityType.FEATURE_CODING: {
            "count": 8,
            "top_file": "real_test/COSC-304-Final-Project/node_modules/pkg/file.js",
        },
        ActivityType.REFACTORING: {"count": 0, "top_file": None},
        ActivityType.DEBUGGING: {"count": 0, "top_file": None},
        ActivityType.TESTING: {"count": 1, "top_file": None},
        ActivityType.DOCUMENTATION: {"count": 1, "top_file": None},
    }

    summary = ActivitySummary(
        project_name="COSC-304-Final-Project",
        scope=Scope.INDIVIDUAL,
        duration_start="2024-01-01",
        duration_end="2024-01-02",
        total_events=10,
        per_activity=per_activity,
    )

    text = format_activity_summary(summary)

    # No header lines
    assert "Project:" not in text
    assert "Scope:" not in text
    assert "Duration:" not in text

    # Has the summary header
    assert "Activity summary (by files/PRs):" in text

    # Feature coding line: 8/10 -> 80.00% and shortened path
    fc_line = next(
        l for l in text.splitlines()
        if l.startswith("- Feature Coding:")
    )
    assert "8/10 -> 80.00%" in fc_line
    assert "COSC-304-Final-Project/node_modules/pkg/file.js" in fc_line
    assert "real_test/" not in fc_line  # prefix stripped

    # Documentation line: 1/10 -> 10.00%
    doc_line = next(
        l for l in text.splitlines()
        if l.startswith("- Documentation:")
    )
    assert "1/10 -> 10.00%" in doc_line


# ---------- build_activity_summary tests (mock DB access) ----------

def test_build_activity_summary_aggregates_counts(monkeypatch):
    """
    build_activity_summary should aggregate counts based on mocked file + PR data:
      - 2 code-ish files → Feature Coding
      - 1 test file → Testing
      - 1 doc file → Documentation
    """
    # --- fake DB rows ---

    fake_classification = {
        "classification": "individual",
        "project_type": "code",
        "recorded_at": "2024-01-01",
    }

    fake_files = [
        # feature coding file
        {
            "file_id": 1,
            "file_name": "main.py",
            "file_path": "COSC-304-Final-Project/src/app/main.py",
            "extension": ".py",
            "file_type": "code",
            "created": "2024-01-01",
            "modified": "2024-01-02",
            "size_bytes": 100,
        },
        # another feature coding file
        {
            "file_id": 2,
            "file_name": "utils.py",
            "file_path": "COSC-304-Final-Project/src/app/utils.py",
            "extension": ".py",
            "file_type": "code",
            "created": "2024-01-01",
            "modified": "2024-01-03",
            "size_bytes": 100,
        },
        # testing file
        {
            "file_id": 3,
            "file_name": "test_main.py",
            "file_path": "COSC-304-Final-Project/tests/test_main.py",
            "extension": ".py",
            "file_type": "code",
            "created": "2024-01-01",
            "modified": "2024-01-04",
            "size_bytes": 100,
        },
        # documentation file
        {
            "file_id": 4,
            "file_name": "README.md",
            "file_path": "COSC-304-Final-Project/README.md",
            "extension": ".md",
            "file_type": "text",
            "created": "2024-01-01",
            "modified": "2024-01-05",
            "size_bytes": 100,
        },
    ]

    fake_prs = [
        {
            "id": 1,
            "pr_number": 10,
            "pr_title": "Refactor and add more tests",
            "pr_body": "This PR adds integration tests and refactors some helpers.",
            "labels_json": "[]",
            "created_at": "2024-01-06",
            "merged_at": "2024-01-07",
            "state": "merged",
            "merged": 1,
        }
    ]

    # --- monkeypatch DB-related functions in summary_mod ---

    monkeypatch.setattr(
        summary_mod,
        "get_project_classification",
        lambda user_id, project_name, db_path=None: fake_classification,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_project_files",
        lambda user_id, project_name, db_path=None: fake_files,
    )
    monkeypatch.setattr(
        summary_mod,
        "is_github_connected",
        lambda user_id, db_path=None: True,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_project_repos",
        lambda user_id, project_name, db_path=None: [{"provider": "github"}],
    )
    monkeypatch.setattr(
        summary_mod,
        "get_project_prs",
        lambda user_id, project_name, db_path=None: fake_prs,
    )

    # --- run build_activity_summary ---

    user_id = 123
    project_name = "COSC-304-Final-Project"
    summary = summary_mod.build_activity_summary(user_id=user_id, project_name=project_name)

    # We have 4 files + 1 PR = 5 events total
    assert summary.total_events == 5

    # Feature coding: 2 files (src/app) + maybe PR classified as feature/refactor/testing
    fc_count = summary.per_activity[ActivityType.FEATURE_CODING]["count"]
    testing_count = summary.per_activity[ActivityType.TESTING]["count"]
    doc_count = summary.per_activity[ActivityType.DOCUMENTATION]["count"]

    # At least: 2 feature coding (src files), 1 testing (test file), 1 documentation (README)
    assert fc_count >= 2
    assert testing_count >= 1
    assert doc_count >= 1

    # Duration should span from earliest created/modified/merged to latest
    assert summary.duration_start is not None
    assert summary.duration_end is not None
