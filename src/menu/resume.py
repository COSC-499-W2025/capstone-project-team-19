"""
src/menu/resume.py

Menu option for viewing resume items.
"""

import json
from typing import List

from src.db import get_all_user_project_summaries
from src.models.project_summary import ProjectSummary


def view_resume_items(conn, user_id: int, username: str):
    """
    Load stored project summaries for the user and prepare them for resume display.
    """
    summaries = _load_project_summaries(conn, user_id)
    print(f"\n[Resume] Loaded {len(summaries)} project summary record(s) for {username}.")
    # Rendering will be added in subsequent steps.
    return summaries


def _load_project_summaries(conn, user_id: int) -> List[ProjectSummary]:
    """
    Fetch and deserialize all saved project summaries for the user.
    """
    rows = get_all_user_project_summaries(conn, user_id)
    projects: List[ProjectSummary] = []

    for row in rows:
        try:
            summary_dict = json.loads(row["summary_json"])
            projects.append(ProjectSummary.from_dict(summary_dict))
        except Exception:
            # Skip malformed entries to avoid breaking the resume flow.
            continue

    return projects
