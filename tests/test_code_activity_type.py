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

def test_format_activity_summary_table_and_shortened_paths():
    """
    format_activity_summary (files-only case) should:
      - print 'Activity summary (files)'
      - show a table row for each activity type
      - shorten top file paths using _shorten_top_file
    """
    # Files-only stats
    per_activity_files = {
        ActivityType.FEATURE_CODING: {
            "count": 8,
            "top_file": "real_test/COSC-304-Final-Project/node_modules/pkg/file.js",
        },
        ActivityType.REFACTORING: {"count": 0, "top_file": None},
        ActivityType.DEBUGGING: {"count": 0, "top_file": None},
        ActivityType.TESTING: {"count": 1, "top_file": None},
        ActivityType.DOCUMENTATION: {"count": 1, "top_file": None},
    }
    # No PRs for this test
    per_activity_prs = {
        at: {"count": 0, "top_pr": None} for at in ActivityType
    }
    # Combined = same as files for this test
    per_activity_total = {
        at: {
            "count": per_activity_files[at]["count"],
            "top_file": per_activity_files[at]["top_file"],
        }
        for at in ActivityType
    }

    summary = ActivitySummary(
        project_name="COSC-304-Final-Project",
        scope=Scope.INDIVIDUAL,
        total_events=10,
        total_file_events=10,
        total_pr_events=0,
        per_activity=per_activity_total,
        per_activity_files=per_activity_files,
        per_activity_prs=per_activity_prs,
        top_file="real_test/COSC-304-Final-Project/node_modules/pkg/file.js",
        top_pr=None,
        top_pr_title=None,
    )

    text = format_activity_summary(summary)

    # No extra header lines
    assert "Project:" not in text
    assert "Scope:" not in text

    lines = text.splitlines()
    # Header should be files-only
    assert lines[0].strip() == "Activity summary (files)"

    # There should be a row containing "Feature Coding" and the count "8"
    fc_line = next(l for l in lines if "Feature Coding" in l)
    assert "8" in fc_line

    # Path should be shortened (no 'real_test/' prefix) in the Top file section
    assert "COSC-304-Final-Project/node_modules/pkg/file.js" in text
    assert "real_test/COSC-304-Final-Project/node_modules/pkg/file.js" not in text

def test_format_activity_summary_with_prs_header():
    """
    When there are both file and PR events, the header should be
    'Activity summary (files vs PRs)' and the PR column should appear.
    Also verifies that the Top PR line includes both the PR number and title.
    """
    per_activity_files = {
        ActivityType.FEATURE_CODING: {"count": 2, "top_file": "proj/src/main.py"},
        ActivityType.REFACTORING: {"count": 0, "top_file": None},
        ActivityType.DEBUGGING: {"count": 0, "top_file": None},
        ActivityType.TESTING: {"count": 0, "top_file": None},
        ActivityType.DOCUMENTATION: {"count": 0, "top_file": None},
    }
    per_activity_prs = {
        ActivityType.FEATURE_CODING: {"count": 1, "top_pr": "pr#10"},
        ActivityType.REFACTORING: {"count": 0, "top_pr": None},
        ActivityType.DEBUGGING: {"count": 0, "top_pr": None},
        ActivityType.TESTING: {"count": 0, "top_pr": None},
        ActivityType.DOCUMENTATION: {"count": 0, "top_pr": None},
    }
    per_activity_total = {
        at: {
            "count": per_activity_files[at]["count"] + per_activity_prs[at]["count"],
            "top_file": per_activity_files[at]["top_file"],
        }
        for at in ActivityType
    }

    summary = ActivitySummary(
        project_name="proj",
        scope=Scope.COLLABORATIVE,
        total_events=3,
        total_file_events=2,
        total_pr_events=1,
        per_activity=per_activity_total,
        per_activity_files=per_activity_files,
        per_activity_prs=per_activity_prs,
        top_file="proj/src/main.py",
        top_pr="pr#10",
        top_pr_title="My PR title",
    )

    text = format_activity_summary(summary)
    lines = text.splitlines()

    # Header should include "files vs PRs"
    assert lines[0].strip() == "Activity summary (files vs PRs)"

    # Table should contain the PR column
    assert any("PRs (# / total %)" in line for line in lines)

    # Top PR must include both number and title
    assert "Top PR: pr#10 (My PR title)" in text

# ---------- build_activity_summary tests (mock DB access) ----------

def test_build_activity_summary_aggregates_counts_individual(monkeypatch):
    """
    build_activity_summary should aggregate counts based on mocked file + PR data
    for an INDIVIDUAL project.
    """
    # --- fake DB rows ---

    fake_classification = ("individual", "code")  # (classification, project_type)

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
        "get_project_metadata",
        lambda conn, user_id, project_name: fake_classification,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_files_for_project",
        lambda conn, user_id, project_name, only_text=False: fake_files,
    )
    # individual path should not use user contributions, but we stub anyway
    monkeypatch.setattr(
        summary_mod,
        "get_user_contributed_files",
        lambda conn, user_id, project_name: [],
    )
    monkeypatch.setattr(
        summary_mod,
        "has_github_account",
        lambda conn, user_id: True,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_project_repo",
        lambda conn, user_id, project_name: "https://github.com/example/repo",
    )
    monkeypatch.setattr(
        summary_mod,
        "get_pull_requests_for_project",
        lambda conn, user_id, project_name: fake_prs,
    )

    # --- run build_activity_summary ---

    conn = object()  # dummy
    user_id = 123
    project_name = "COSC-304-Final-Project"
    summary = summary_mod.build_activity_summary(conn, user_id=user_id, project_name=project_name)

    # We have 4 file events + 1 PR event = 5 total events
    assert summary.total_events == 5
    assert summary.total_file_events == 4
    assert summary.total_pr_events == 1

    fc_count = summary.per_activity[ActivityType.FEATURE_CODING]["count"]
    testing_count = summary.per_activity[ActivityType.TESTING]["count"]
    doc_count = summary.per_activity[ActivityType.DOCUMENTATION]["count"]

    # At least: 2 feature coding (src files), 1 testing (test file), 1 documentation (README)
    assert fc_count >= 2
    assert testing_count >= 1
    assert doc_count >= 1

    # Top PR should be filled with the PR number
    assert summary.top_pr == "pr#10" or summary.top_pr == "pr#10"


def test_build_activity_summary_collaborative_uses_contributed_files_only(monkeypatch):
    """
    For COLLABORATIVE projects, build_activity_summary should only count files
    that appear in the user_file_contributions list (by filename).
    """
    fake_classification = ("collaborative", "code")

    fake_files = [
        {
            "file_id": 1,
            "file_name": "main.py",
            "file_path": "proj/src/main.py",
            "extension": ".py",
            "file_type": "code",
            "created": "2024-01-01",
            "modified": "2024-01-02",
            "size_bytes": 100,
        },
        {
            "file_id": 2,
            "file_name": "ignore_me.py",
            "file_path": "proj/src/ignore_me.py",
            "extension": ".py",
            "file_type": "code",
            "created": "2024-01-01",
            "modified": "2024-01-02",
            "size_bytes": 100,
        },
    ]

    # user_file_contributions stores only filenames (e.g., "main.py")
    monkeypatch.setattr(
        summary_mod,
        "get_project_metadata",
        lambda conn, user_id, project_name: fake_classification,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_files_for_project",
        lambda conn, user_id, project_name, only_text=False: fake_files,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_user_contributed_files",
        lambda conn, user_id, project_name: ["main.py"],
    )
    monkeypatch.setattr(
        summary_mod,
        "has_github_account",
        lambda conn, user_id: False,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_project_repo",
        lambda conn, user_id, project_name: None,
    )
    monkeypatch.setattr(
        summary_mod,
        "get_pull_requests_for_project",
        lambda conn, user_id, project_name: [],
    )

    conn = object()
    user_id = 1
    project_name = "proj"
    summary = summary_mod.build_activity_summary(conn, user_id, project_name)

    # Only 1 file should be counted (main.py), not ignore_me.py
    assert summary.total_file_events == 1
    assert summary.total_events == 1
