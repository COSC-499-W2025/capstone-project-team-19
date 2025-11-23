"""
Defines core enums and dataclasses for activity type detection and summaries.
Used across fetch, labeler, summary, and formatter modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ActivityType(str, Enum):
    FEATURE_CODING = "feature_coding"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class Scope(str, Enum):
    INDIVIDUAL = "individual"
    COLLABORATIVE = "collaborative"


@dataclass
class ActivityEvent:
    """
    One detected activity event (file-based or PR-based).
    """
    project_name: str
    scope: Scope
    source: str               # "file" or "pr"
    event_id: str             # file_id/file_name or "pr#123"
    timestamp: Optional[str]  # file.modified or PR merged_at/created_at
    activity_type: ActivityType
    files: List[str]          # file paths; empty for PR-only events
    message_text: str         # filename or PR title/body extract


@dataclass
class ActivitySummary:
    """
    Per-project aggregated summary of activity types and top files.
    """
    project_name: str
    scope: Scope
    duration_start: Optional[str]
    duration_end: Optional[str]
    total_events: int
    per_activity: Dict[ActivityType, Dict[str, Optional[str]]]
    # Example entry:
    # {
    #   ActivityType.FEATURE_CODING: {"count": 22, "top_file": "src/main.py"},
    #   ActivityType.TESTING:        {"count": 6,  "top_file": "tests/test_foo.py"},
    # }
