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
    Per-project aggregated summary of activity types and top files/PRs.
    """
    project_name: str
    scope: Scope

    # Totals
    total_events: int              # files + PRs
    total_file_events: int         # only file-based events
    total_pr_events: int           # only PR-based events

    # Activity breakdown
    per_activity: Dict[ActivityType, Dict[str, Optional[str]]]          # combined
    per_activity_files: Dict[ActivityType, Dict[str, Optional[str]]]
    per_activity_prs: Dict[ActivityType, Dict[str, Optional[str]]]

    # Top items
    top_file: Optional[str] = None
    top_pr: Optional[str] = None
    top_pr_title: Optional[str] = None
