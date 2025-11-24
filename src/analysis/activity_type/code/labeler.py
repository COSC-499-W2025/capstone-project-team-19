"""
Converts raw DB rows (files, PRs) into ActivityEvent objects using rules.
Handles scoring, tie-breaking, and default fallbacks.
"""

from __future__ import annotations

from typing import Dict, List

from .rules import infer_activity_from_filename, infer_activity_from_pr_text
from .types import ActivityEvent, ActivityType, Scope


def _pick_final_activity(score_dict: Dict[ActivityType, int]) -> ActivityType:
    """
    Pick ActivityType with highest score, using fixed priority on ties.
    Priority: TESTING > DOCUMENTATION > DEBUGGING > REFACTORING > FEATURE_CODING
    """
    priority = [
        ActivityType.TESTING,
        ActivityType.DOCUMENTATION,
        ActivityType.DEBUGGING,
        ActivityType.REFACTORING,
        ActivityType.FEATURE_CODING,
    ]

    max_score = max(score_dict.values()) if score_dict else 0
    if max_score == 0:
        return ActivityType.FEATURE_CODING

    candidates = [at for at, s in score_dict.items() if s == max_score]
    for at in priority:
        if at in candidates:
            return at

    return ActivityType.FEATURE_CODING


def label_file_event(
    project_name: str,
    scope: Scope,
    file_row: dict,
) -> ActivityEvent:
    """
    Label a single offline file row as an ActivityEvent based on filename/path.
    """
    file_name = file_row.get("file_name", "")
    file_path = file_row.get("file_path") or ""
    modified = file_row.get("modified")

    scores = infer_activity_from_filename(file_name, file_path)
    activity = _pick_final_activity(scores)

    event_id = str(file_row.get("file_id", file_name))
    files: List[str] = [file_path or file_name]

    return ActivityEvent(
        project_name=project_name,
        scope=scope,
        source="file",
        event_id=event_id,
        timestamp=modified,
        activity_type=activity,
        files=files,
        message_text=file_name,
    )


def label_pr_event(
    project_name: str,
    scope: Scope,
    pr_row: dict,
) -> ActivityEvent:
    """
    Label a single PR row as an ActivityEvent based on title/body text.
    """
    title = pr_row.get("pr_title") or ""
    body = pr_row.get("pr_body") or ""
    merged_at = pr_row.get("merged_at") or pr_row.get("created_at")

    scores = infer_activity_from_pr_text(title, body)
    activity = _pick_final_activity(scores)

    pr_number = pr_row.get("pr_number")
    event_id = f"pr#{pr_number}" if pr_number is not None else str(pr_row.get("id"))

    files: List[str] = []  # can be filled later if you join PR → changed files
    message = title.strip() or "(no title)"

    return ActivityEvent(
        project_name=project_name,
        scope=scope,
        source="pr",
        event_id=event_id,
        timestamp=merged_at,
        activity_type=activity,
        files=files,
        message_text=message,
    )
