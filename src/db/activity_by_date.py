"""
src/db/activity_by_date.py

Aggregates activity counts by date for the GitHub-style contribution heatmap.
Uses project date ranges (start_date to end_date): for each day in a project's
range, that project counts toward that day. More projects overlapping a day = darker green.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from collections import defaultdict


def get_activity_counts_by_date(
    conn,
    user_id: int,
    project_ids: Optional[Set[int]] = None,
) -> tuple[Dict[str, int], Dict[str, list[str]]]:
    """
    Returns (counts, projects_by_date).
    counts: date (YYYY-MM-DD) -> count of projects active that day.
    projects_by_date: date -> list of project names active that day.
    A project is "active" on a day if that day falls between its start_date and end_date.
    If project_ids is provided, only those projects are included.
    """
    from src.services.project_dates_service import list_project_dates

    projects_by_date: Dict[str, set] = defaultdict(set)

    items = list_project_dates(conn, user_id)
    if project_ids is not None:
        items = [item for item in items if item.project_summary_id in project_ids]

    for item in items:
        start = item.start_date
        end = item.end_date
        if not start or not end:
            continue

        try:
            start_dt = datetime.strptime(start[:10], "%Y-%m-%d").date()
            end_dt = datetime.strptime(end[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        if start_dt > end_dt:
            continue

        # Add this project to every day in its range
        d = start_dt
        while d <= end_dt:
            key = d.strftime("%Y-%m-%d")
            projects_by_date[key].add(item.project_name)
            d += timedelta(days=1)

    counts = {d: len(projs) for d, projs in projects_by_date.items()}
    projects_dict = {d: sorted(projs) for d, projs in projects_by_date.items()}
    return counts, projects_dict
