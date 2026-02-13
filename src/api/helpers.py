"""
Shared helpers for API routes.
"""

from sqlite3 import Connection
from typing import Optional

from src.db.project_summaries import get_project_summary_by_id


def resolve_project_name_for_edit(conn: Connection, user_id: int, project_summary_id: Optional[int], project_name: Optional[str]) -> Optional[str]:
    """Resolve project_summary_id or project_name to project_name."""
    if project_summary_id is not None:
        row = get_project_summary_by_id(conn, user_id, project_summary_id)
        if row:
            return row.get("project_name")
    return project_name or None