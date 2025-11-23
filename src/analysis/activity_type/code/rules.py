"""
Implements simple heuristic scoring rules for filenames and PR text.
Returns per-ActivityType scores that labeler.py converts to a final label.
"""

from __future__ import annotations

from typing import Dict

from .types import ActivityType


def _init_score_dict() -> Dict[ActivityType, int]:
    return {at: 0 for at in ActivityType}


def infer_activity_from_filename(file_name: str, file_path: str) -> Dict[ActivityType, int]:
    """
    Score activities based on filename + path (tests/docs/src...).
    """
    name = (file_name or "").lower()
    path = (file_path or "").lower()

    scores = _init_score_dict()

    # Testing: tests directory or test_* / *_test pattern
    if (
        "tests/" in path
        or "/test/" in path
        or name.startswith("test_")
        or name.endswith("_test.py")
    ):
        scores[ActivityType.TESTING] += 2

    # Documentation: docs folder, README, markdown/rst
    if (
        "docs/" in path
        or name.startswith("readme")
        or name.endswith(".md")
        or name.endswith(".rst")
    ):
        scores[ActivityType.DOCUMENTATION] += 2

    # Feature coding: typical implementation directories
    if "src/" in path or "/app/" in path or "/lib/" in path:
        scores[ActivityType.FEATURE_CODING] += 1

    return scores


def infer_activity_from_pr_text(title: str, body: str) -> Dict[ActivityType, int]:
    """
    Score activities based on PR title + body keywords.
    """
    text = f"{title or ''}\n{body or ''}".lower()
    scores = _init_score_dict()

    # Testing
    if any(k in text for k in ["test", "unit test", "integration test", "coverage"]):
        scores[ActivityType.TESTING] += 1

    # Documentation
    if any(k in text for k in ["doc", "docs", "documentation", "readme", "changelog"]):
        scores[ActivityType.DOCUMENTATION] += 1

    # Debugging / bugfix
    if any(k in text for k in ["fix", "bug", "error", "crash", "hotfix", "patch", "issue"]):
        scores[ActivityType.DEBUGGING] += 2

    # Refactoring
    if any(k in text for k in ["refactor", "cleanup", "restructure", "rename", "simplify"]):
        scores[ActivityType.REFACTORING] += 2

    # Feature coding
    if any(k in text for k in ["add", "implement", "create", "feature", "support", "initial", "prototype"]):
        scores[ActivityType.FEATURE_CODING] += 1

    return scores
