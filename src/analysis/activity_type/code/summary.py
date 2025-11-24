"""
Builds an ActivitySummary per project by combining file and PR events.
Uses src.db helpers + labeler.py to get events, then aggregates counts and top items.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Dict, List, Optional, Tuple

from src.db import (
    get_project_metadata,
    get_files_for_project,
    get_user_contributed_files,
    get_project_repo,
    has_github_account,
    get_pull_requests_for_project,
)

from .labeler import label_file_event, label_pr_event
from .types import ActivityEvent, ActivitySummary, ActivityType, Scope
from src.analysis.code_individual.code_complexity_analyzer import EXCLUDE_DIRECTORIES

def _aggregate_per_activity(
    events: List[ActivityEvent],
) -> Tuple[
    Dict[ActivityType, Dict[str, Optional[str]]],  # per_activity_files
    Dict[ActivityType, Dict[str, Optional[str]]],  # per_activity_prs
    Dict[ActivityType, Dict[str, Optional[str]]],  # per_activity_total
    int,                                           # total_file_events
    int,                                           # total_pr_events
    Optional[str],                                 # top_file_overall
    Optional[str],                                 # top_pr_overall
    Optional[str],                                 # top_pr_title_overall
]:
    """
    Aggregate events into per-activity stats for:
      - file-only events
      - PR-only events
      - combined (files + PRs)

    Also returns:
      - total file events
      - total PR events
      - overall top file path
      - overall top PR id
      - overall top PR title
    """
    # Counts per activity type
    total_counts: Counter[ActivityType] = Counter()
    file_counts: Counter[ActivityType] = Counter()
    pr_counts: Counter[ActivityType] = Counter()

    # File paths per activity (files-only vs combined)
    file_paths_files: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }
    file_paths_total: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }

    # PR ids per activity
    pr_ids_per_activity: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }

    # Global top-tracking
    global_file_paths: Counter[str] = Counter()
    global_pr_ids: Counter[str] = Counter()
    global_pr_titles: Dict[str, str] = {}

    for e in events:
        at = e.activity_type
        total_counts[at] += 1

        # Track files (for both file + PR events if they have files)
        for f in e.files:
            if not f:
                continue
            file_paths_total[at][f] += 1
            global_file_paths[f] += 1

            if e.source == "file":
                file_paths_files[at][f] += 1

        # File vs PR counts
        if e.source == "file":
            file_counts[at] += 1
        elif e.source == "pr":
            pr_counts[at] += 1
            pr_id = e.event_id or e.message_text
            if pr_id:
                pr_ids_per_activity[at][pr_id] += 1
                global_pr_ids[pr_id] += 1
                # message_text is our best "title" for the PR
                if e.message_text:
                    global_pr_titles[pr_id] = e.message_text

    per_files: Dict[ActivityType, Dict[str, Optional[str]]] = {}
    per_prs: Dict[ActivityType, Dict[str, Optional[str]]] = {}
    per_total: Dict[ActivityType, Dict[str, Optional[str]]] = {}

    for at in ActivityType:
        # Files-only stats
        f_count = file_counts.get(at, 0)
        f_top = None
        if file_paths_files[at]:
            f_top = file_paths_files[at].most_common(1)[0][0]
        per_files[at] = {"count": f_count, "top_file": f_top}

        # PR-only stats
        p_count = pr_counts.get(at, 0)
        p_top = None
        if pr_ids_per_activity[at]:
            p_top = pr_ids_per_activity[at].most_common(1)[0][0]
        per_prs[at] = {"count": p_count, "top_pr": p_top}

        # Combined stats (files + PRs); use overall top file per activity
        t_count = total_counts.get(at, 0)
        t_top_file = None
        if file_paths_total[at]:
            t_top_file = file_paths_total[at].most_common(1)[0][0]
        per_total[at] = {"count": t_count, "top_file": t_top_file}

    total_file_events = sum(file_counts.values())
    total_pr_events = sum(pr_counts.values())

    top_file_overall: Optional[str] = None
    if global_file_paths:
        top_file_overall = global_file_paths.most_common(1)[0][0]

    top_pr_overall: Optional[str] = None
    top_pr_title_overall: Optional[str] = None
    if global_pr_ids:
        top_pr_overall = global_pr_ids.most_common(1)[0][0]
        top_pr_title_overall = global_pr_titles.get(top_pr_overall)

    return (
        per_files,
        per_prs,
        per_total,
        total_file_events,
        total_pr_events,
        top_file_overall,
        top_pr_overall,
        top_pr_title_overall,
    )


def _resolve_scope_from_metadata(classification: Optional[str]) -> Scope:
    """
    Map classification string to Scope enum; default to COLLABORATIVE.
    """
    if classification == "individual":
        return Scope.INDIVIDUAL
    return Scope.COLLABORATIVE


def build_activity_summary(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
) -> ActivitySummary:
    """
    Main entry: fetch classification, files, optional PRs and return ActivitySummary.

    - Uses src/db helpers (no inline SQL here)
    - For collaborative projects, file events are restricted to files the user actually
      contributed to (via user_file_contributions)
    - For individual projects, all files for this user + project are used
    """
    # 1) Classification → scope
    classification, _project_type = get_project_metadata(conn, user_id, project_name)
    scope = _resolve_scope_from_metadata(classification)

    events: List[ActivityEvent] = []

    # 2) File-based events
    all_files_raw = get_files_for_project(conn, user_id, project_name, only_text=False)

    # Filter out dependency/vendor directories
    all_files = [
        f for f in all_files_raw
        if not _is_excluded_dependency(f.get("file_path"))
    ]

    if scope == Scope.COLLABORATIVE:
        # Restrict to files the user actually contributed to
        contributed_filenames = set(
            p.split("/")[-1]  # safety in case path appears
            for p in get_user_contributed_files(conn, user_id, project_name)
        )

        file_rows = [
            f for f in all_files
            if f.get("file_name") in contributed_filenames
        ]
    else:
        # Individual → all files for this user + project
        file_rows = all_files

    for row in file_rows:
        events.append(label_file_event(project_name, scope, row))

    # 3) PR-based events (if GitHub linked and repo mapped)
    github_ok = has_github_account(conn, user_id)
    repo_url = get_project_repo(conn, user_id, project_name)

    if github_ok and repo_url:
        pr_rows = get_pull_requests_for_project(conn, user_id, project_name)
        for pr in pr_rows:
            events.append(label_pr_event(project_name, scope, pr))

    # 4) Aggregate per-activity stats
    (
        per_activity_files,
        per_activity_prs,
        per_activity_total,
        total_file_events,
        total_pr_events,
        top_file,
        top_pr,
        top_pr_title,
    ) = _aggregate_per_activity(events)

    return ActivitySummary(
        project_name=project_name,
        scope=scope,
        total_events=len(events),
        total_file_events=total_file_events,
        total_pr_events=total_pr_events,
        per_activity=per_activity_total,
        per_activity_files=per_activity_files,
        per_activity_prs=per_activity_prs,
        top_file=top_file,
        top_pr=top_pr,
        top_pr_title=top_pr_title,
    )

def _is_excluded_dependency(path: str | None) -> bool:
    if not path:
        return False

    path = path.replace("\\", "/")

    # match folder names
    for dirname in EXCLUDE_DIRECTORIES:
        # match ".../dirname/" or ".../dirname\"
        if f"/{dirname}/" in path:
            return True

    return False
