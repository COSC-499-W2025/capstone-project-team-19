from __future__ import annotations

from contextlib import nullcontext
from sqlite3 import Connection
from typing import Any, Dict, List, Optional

from src.db import get_project_summary_by_id
from src.insights.rank_projects.rank_project_importance import collect_project_ranking_rows
from src.services.project_rankings_write_service import (
    bulk_set_rankings,
    clear_all_rankings,
    clear_project_rank,
    set_project_rank,
)


def get_project_ranking(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    """
    Returns sorted ranking rows (including score + manual rank).
    """
    return collect_project_ranking_rows(conn, user_id, respect_manual_ranking=True)


def replace_project_ranking(conn: Connection, user_id: int, project_ids: List[int]) -> None:
    """
    Replace the ENTIRE manual ranking order for this user.

    project_ids are project_summary_ids. Behavior:
    - Clears all existing manual ranks
    - Sets manual_rank = 1..N according to the provided project_ids order
    """
    if len(project_ids) != len(set(project_ids)):
        raise ValueError("Duplicate project IDs are not allowed")

    # Validate all ids exist + belong to user, and map to project_key
    project_keys: List[int] = []
    for pid in project_ids:
        row = get_project_summary_by_id(conn, user_id, pid)
        if not row:
            raise KeyError(f"Project not found: {pid}")
        project_keys.append(row["project_key"])

    # "replace" performs multiple writes. Use a single transaction so callers
    # never observe a partially-cleared/partially-inserted ranking set.
    with (conn if not conn.in_transaction else nullcontext(conn)):
        clear_all_rankings(conn, user_id)
        rankings = [(pk, rank) for rank, pk in enumerate(project_keys, start=1)]
        bulk_set_rankings(conn, user_id, rankings)


def set_project_manual_rank(conn: Connection, user_id: int, project_id: int, rank: Optional[int]) -> None:
    """
    Patch one project's manual rank. If rank is None, clears manual ranking for that project.
    project_id is project_summary_id.
    """
    row = get_project_summary_by_id(conn, user_id, project_id)
    if not row:
        raise KeyError(f"Project not found: {project_id}")
    project_key = row["project_key"]

    if rank is None:
        clear_project_rank(conn, user_id, project_key)
        return

    set_project_rank(conn, user_id, project_key, rank)


def reset_project_ranking(conn: Connection, user_id: int) -> None:
    """
    Clears all manual ranking for the user (reverts to pure auto ranking).
    """
    clear_all_rankings(conn, user_id)

