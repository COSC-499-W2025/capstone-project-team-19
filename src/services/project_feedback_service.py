from __future__ import annotations

from sqlite3 import Connection
from typing import Any, Dict, Optional

from src.db import get_project_summary_by_id
from src.db.project_feedback import get_project_feedback


def get_project_feedback_by_project_id(conn: Connection, user_id: int, project_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns a ProjectFeedbackDTO-shaped dict for one project.

    Note: `{project_id}` maps to `project_summaries.project_summary_id`, while feedback is stored keyed by `project_name`.
    """

    project_row = get_project_summary_by_id(conn, user_id, project_id)
    if not project_row: return None

    project_name = project_row["project_name"]
    feedback_rows = get_project_feedback(conn, user_id, project_name)

    return {
        "project_id": project_id,
        "project_name": project_name,
        "feedback": feedback_rows,
    }