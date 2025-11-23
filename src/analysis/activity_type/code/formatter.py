"""
Formats an ActivitySummary into a human-readable multi-line string.
Used for printing in the terminal or logs.
"""

from __future__ import annotations
from .types import ActivitySummary, ActivityType, Scope

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
    Format ActivitySummary into a human-readable table.

    Cases:
      - If PR events exist: show files vs PRs vs combined.
      - If no PR events: show files-only table.
    """
    lines: list[str] = []

    has_prs = summary.total_pr_events > 0

    # ----- Title -----
    if has_prs:
        title = "Activity summary (files vs PRs)"
    else:
        if summary.scope == Scope.INDIVIDUAL:
            title = "Activity summary (files)"
        else:
            title = "Activity summary (files – GitHub not connected)"

    lines.append(title)
    lines.append("")

    # ----- Helper to format "n (xx.x%)" safely -----
    def fmt_count_pct(count: int, total: int) -> str:
        if total <= 0:
            return f"{count} (0.0%)"
        pct = (count / total) * 100.0
        return f"{count} ({pct:.1f}%)"

    # ----- Case 1: files vs PRs vs combined -----
    if has_prs:
        header = (
            f"{'Activity':<16}"
            f"{'Files (# / total %)':<26}"
            f"{'PRs (# / total %)':<26}"
            f"{'Combined (# / total %)'}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for at in ActivityType:
            files_entry = summary.per_activity_files.get(at, {})
            prs_entry = summary.per_activity_prs.get(at, {})
            total_entry = summary.per_activity.get(at, {})

            f_count = int(files_entry.get("count", 0) or 0)
            p_count = int(prs_entry.get("count", 0) or 0)
            t_count = int(total_entry.get("count", 0) or 0)

            files_str = fmt_count_pct(f_count, summary.total_file_events)
            prs_str = fmt_count_pct(p_count, summary.total_pr_events)
            total_str = fmt_count_pct(t_count, summary.total_events)

            lines.append(
                f"{at.name.replace('_', ' ').title():<16}"
                f"{files_str:<26}"
                f"{prs_str:<26}"
                f"{total_str}"
            )

        # TOTAL row
        lines.append("-" * len(header))
        total_files_str = fmt_count_pct(summary.total_file_events, summary.total_file_events)
        total_prs_str = fmt_count_pct(summary.total_pr_events, summary.total_pr_events)
        total_combined_str = fmt_count_pct(summary.total_events, summary.total_events)

        lines.append(
            f"{'TOTAL':<16}"
            f"{total_files_str:<26}"
            f"{total_prs_str:<26}"
            f"{total_combined_str}"
        )

    # ----- Case 2: files-only (no PRs) -----
    else:
        header = f"{'Activity':<16}{'Files (# / total %)'}"
        lines.append(header)
        lines.append("-" * len(header))

        for at in ActivityType:
            files_entry = summary.per_activity_files.get(at, {})
            f_count = int(files_entry.get("count", 0) or 0)
            files_str = fmt_count_pct(f_count, summary.total_file_events)

            lines.append(
                f"{at.name.replace('_', ' ').title():<16}{files_str}"
            )

        lines.append("-" * len(header))
        total_files_str = fmt_count_pct(summary.total_file_events, summary.total_file_events)
        lines.append(f"{'TOTAL':<16}{total_files_str}")

    # ----- Top items -----
    top_lines: list[str] = []

    if summary.top_file:
        shortened = _shorten_top_file(summary.top_file, summary.project_name)
        top_lines.append(f"- Top file: {shortened}")

    if has_prs and summary.top_pr:
        if summary.top_pr:
            if summary.top_pr_title:
                top_lines.append(f"- Top PR: {summary.top_pr} ({summary.top_pr_title})")
            else:
                top_lines.append(f"- Top PR: {summary.top_pr}")

    if top_lines:
        lines.append("")
        lines.append("Top items:")
        lines.extend(top_lines)

    return "\n".join(lines)
