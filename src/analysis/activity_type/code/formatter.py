"""
Formats an ActivitySummary into a human-readable multi-line string.
Used for printing in the terminal or logs.
"""

from __future__ import annotations

from .types import ActivitySummary, ActivityType, Scope


def _scope_to_string(scope: Scope) -> str:
    if scope == Scope.INDIVIDUAL:
        return "Individual"
    if scope == Scope.COLLABORATIVE:
        return "Collaborative"
    return str(scope.value)


def format_activity_summary(summary: ActivitySummary) -> str:
    """
    Return printable overview, including duration and per-activity counts.
    """
    lines = []

    lines.append(f"=== Project: {summary.project_name} ===")
    lines.append(f"Scope: {_scope_to_string(summary.scope)}")

    if summary.duration_start and summary.duration_end:
        lines.append(f"Duration: {summary.duration_start} \u2192 {summary.duration_end}")
    else:
        lines.append("Duration: (no timestamps available)")

    lines.append("")
    lines.append("Activity summary (by files/PRs):")

    total = max(summary.total_events, 1)  # avoid divide-by-zero semantics

    for at in ActivityType:
        entry = summary.per_activity.get(at, {})
        count = entry.get("count", 0)
        top_file = entry.get("top_file")

        label = at.name.replace("_", " ").title()
        line = f"- {label}: {count}/{summary.total_events}"

        if top_file:
            line += f" (top file: {top_file})"

        lines.append(line)

    return "\n".join(lines)
