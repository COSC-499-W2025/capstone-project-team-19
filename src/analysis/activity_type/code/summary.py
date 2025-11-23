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
]:
    """
    Return:
      - per-activity for files, PRs, and combined
      - total counts for files/PRs
      - global top file / top PR (for footer)
    """
    from collections import Counter

    # Counts per activity
    total_counts: Counter[ActivityType] = Counter()
    file_counts: Counter[ActivityType] = Counter()
    pr_counts: Counter[ActivityType] = Counter()

    # File path counts per activity
    file_paths_files: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }
    file_paths_total: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }

    # PR id/title counts per activity
    pr_ids_per_activity: Dict[ActivityType, Counter[str]] = {
        at: Counter() for at in ActivityType
    }

    # Global top file / PR
    global_file_paths: Counter[str] = Counter()
    global_pr_ids: Counter[str] = Counter()

    for e in events:
        at = e.activity_type
        total_counts[at] += 1

        # Any files attached to the event (mostly file-based events)
        for f in e.files:
            if not f:
                continue
            file_paths_total[at][f] += 1
            global_file_paths[f] += 1

            if e.source == "file":
                file_paths_files[at][f] += 1

        if e.source == "file":
            file_counts[at] += 1
        elif e.source == "pr":
            pr_counts[at] += 1
            pr_id = e.event_id or e.message_text
            if pr_id:
                pr_ids_per_activity[at][pr_id] += 1
                global_pr_ids[pr_id] += 1

    per_files: Dict[ActivityType, Dict[str, Optional[str]]] = {}
    per_prs: Dict[ActivityType, Dict[str, Optional[str]]] = {}
    per_total: Dict[ActivityType, Dict[str, Optional[str]]] = {}

    for at in ActivityType:
        # Files
        f_count = file_counts.get(at, 0)
        f_top = None
        if file_paths_files[at]:
            f_top = file_paths_files[at].most_common(1)[0][0]
        per_files[at] = {"count": f_count, "top_file": f_top}

        # PRs
        p_count = pr_counts.get(at, 0)
        p_top = None
        if pr_ids_per_activity[at]:
            p_top = pr_ids_per_activity[at].most_common(1)[0][0]
        per_prs[at] = {"count": p_count, "top_pr": p_top}

        # Combined (files + PRs); use overall top file
        t_count = total_counts.get(at, 0)
        t_top_file = None
        if file_paths_total[at]:
            t_top_file = file_paths_total[at].most_common(1)[0][0]
        per_total[at] = {"count": t_count, "top_file": t_top_file}

    total_file_events = sum(file_counts.values())
    total_pr_events = sum(pr_counts.values())

    top_file_overall = None
    if global_file_paths:
        top_file_overall = global_file_paths.most_common(1)[0][0]

    top_pr_overall = None
    if global_pr_ids:
        top_pr_overall = global_pr_ids.most_common(1)[0][0]

    return (
        per_files,
        per_prs,
        per_total,
        total_file_events,
        total_pr_events,
        top_file_overall,
        top_pr_overall,
    )

def build_activity_summary(
    user_id: int,
    project_name: str,
    db_path: Optional[str] = None,
) -> ActivitySummary:
    """
    Builds an ActivitySummary for a project.

    - Individual: includes all project files
    - Collaborative: includes only files where the user actually contributed
    - PRs included only if GitHub is connected + repo linked
    """
    classification_row = get_project_classification(user_id, project_name, db_path=db_path)
    scope = resolve_scope(classification_row)

    events: List[ActivityEvent] = []

    # --- File-based events ---
    if scope == Scope.COLLABORATIVE:
        file_rows = get_user_contributed_files(user_id, project_name, db_path=db_path)
    else:
        file_rows = get_project_files(user_id, project_name, db_path=db_path)

    for row in file_rows:
        events.append(label_file_event(project_name, scope, row))

    # --- PR-based events (only if GitHub linked) ---
    github_ok = is_github_connected(user_id, db_path=db_path)
    repos = get_project_repos(user_id, project_name, db_path=db_path)
    has_github_repo = any(r.get("provider") == "github" for r in repos)

    if github_ok and has_github_repo:
        pr_rows = get_project_prs(user_id, project_name, db_path=db_path)
        for pr in pr_rows:
            events.append(label_pr_event(project_name, scope, pr))

    # --- Activity aggregation (files + PRs + totals) ---
    (
        per_activity_files,
        per_activity_prs,
        per_activity_total,
        total_file_events,
        total_pr_events,
        top_file,
        top_pr,
    ) = _aggregate_per_activity(events)

    return ActivitySummary(
        project_name=project_name,
        scope=scope,
        total_events=len(events),
        total_file_events=total_file_events,
        total_pr_events=total_pr_events,
        per_activity=per_activity_total,         # combined
        per_activity_files=per_activity_files,
        per_activity_prs=per_activity_prs,
        top_file=top_file,
        top_pr=top_pr,
    )
