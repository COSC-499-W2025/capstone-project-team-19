"""
Builds an ActivitySummary per project by combining file and PR events.
Uses fetch.py + labeler.py to get events, then aggregates counts and top files.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from .fetch import (
    get_project_classification,
    get_project_files,
    get_project_prs,
    get_project_repos,
    is_github_connected,
    resolve_scope,
    get_user_contributed_files
)
from .labeler import label_file_event, label_pr_event
from .types import ActivityEvent, ActivitySummary, ActivityType, Scope


def _compute_duration(events: List[ActivityEvent]) -> Tuple[Optional[str], Optional[str]]:
    """
    Compute (min_timestamp, max_timestamp) across all events that have timestamps.
    """
    timestamps = [e.timestamp for e in events if e.timestamp]
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


def _aggregate_per_activity(events: List[ActivityEvent]) -> Dict[ActivityType, Dict[str, Optional[str]]]:
    """
    Return {ActivityType: {"count": int, "top_file": str or None}} from events.
    """
    counts: Counter[ActivityType] = Counter()
    file_counts: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }

    for e in events:
        counts[e.activity_type] += 1
        for f in e.files:
            if not f:
                continue
            file_counts[e.activity_type][f] += 1

    result: Dict[ActivityType, Dict[str, Optional[str]]] = {}
    for at in ActivityType:
        count = counts.get(at, 0)
        top_file: Optional[str] = None
        if file_counts[at]:
            top_file = file_counts[at].most_common(1)[0][0]
        result[at] = {"count": count, "top_file": top_file}

    return result


def build_activity_summary(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> ActivitySummary:
    """
    Main entry: fetch classification, files, optional PRs and return ActivitySummary.
    """
    classification_row = get_project_classification(user_id, project_name, db_path=db_path)
    scope = resolve_scope(classification_row)

    events: List[ActivityEvent] = []

    # 1) Offline file events
    if scope == Scope.COLLABORATIVE:
        # Only count files the user actually contributed to
        file_rows = get_user_contributed_files(user_id, project_name, db_path=db_path)
    else:
        # Individual projects: use all project files for this user
        file_rows = get_project_files(user_id, project_name, db_path=db_path)

    for row in file_rows:
        events.append(label_file_event(project_name, scope, row))

    # 2) PR events if GitHub connected and repo linked
    github_ok = is_github_connected(user_id, db_path=db_path)
    repos = get_project_repos(user_id, project_name, db_path=db_path)
    has_github_repo = any(r.get("provider") == "github" for r in repos)

    if github_ok and has_github_repo:
        prs = get_project_prs(user_id, project_name, db_path=db_path)
        for pr in prs:
            events.append(label_pr_event(project_name, scope, pr))

    duration_start, duration_end = _compute_duration(events)
    per_activity = _aggregate_per_activity(events)

    return ActivitySummary(
        project_name=project_name,
        scope=scope,
        duration_start=duration_start,
        duration_end=duration_end,
        total_events=len(events),
        per_activity=per_activity,
    )
