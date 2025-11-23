"""
Formats an ActivitySummary into a human-readable multi-line string.
Used for printing in the terminal or logs.
"""

from __future__ import annotations
from .types import ActivitySummary, ActivityType

def _shorten_top_file(path: str | None, project_name: str = "") -> str | None:
    """
    Remove any leading folders before the actual project name.
    """
    if not path:
        return path

    if project_name and project_name in path:
        idx = path.find(project_name)
        return path[idx:]  # keep from project_name → end

    # fallback (previous behavior)
    marker = "node_modules/"
    idx = path.find(marker)
    return path[idx:] if idx != -1 else path

def format_activity_summary(summary: ActivitySummary) -> str:
    """
    Print ONLY the activity summary — no project name, no scope, no duration.
    """
    lines = []
    lines.append("Activity summary (by files/PRs):")

    total = summary.total_events if summary.total_events > 0 else 1

    for at in ActivityType:
        entry = summary.per_activity.get(at, {})
        count = entry.get("count", 0)
        top_file = entry.get("top_file")

        pct = (count / total) * 100.0
        label = at.name.replace("_", " ").title()
        display_top = _shorten_top_file(top_file, summary.project_name) if top_file else None

        line = f"- {label}: {count}/{summary.total_events} -> {pct:.2f}%"
        if display_top:
            line += f" (top file: {display_top})"

        lines.append(line)

    return "\n".join(lines)
