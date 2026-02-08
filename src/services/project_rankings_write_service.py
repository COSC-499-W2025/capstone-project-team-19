from __future__ import annotations

from contextlib import nullcontext
from sqlite3 import Connection
from typing import List, Optional, Tuple

from src.db.project_rankings import (
    bulk_set_rankings as bulk_set_rankings_query,
    clear_all_rankings as clear_all_rankings_query,
    clear_project_rank as clear_project_rank_query,
    get_project_rank,
    shift_project_ranks_for_insert,
    shift_project_ranks_for_move_down,
    shift_project_ranks_for_move_up,
    upsert_project_rank,
)

def _transaction_scope(conn: Connection):
    """
    Start a transaction if one isn't already active.

    - If we start it, exiting the context commits (or rolls back on exception).
    - If a caller already started one, we don't interfere with their boundaries.
    """
    return conn if not conn.in_transaction else nullcontext(conn)

def clear_project_rank(conn: Connection, user_id: int, project_key: int) -> None:
    with _transaction_scope(conn):
        clear_project_rank_query(conn, user_id, project_key)

def clear_all_rankings(conn: Connection, user_id: int) -> None:
    with _transaction_scope(conn):
        clear_all_rankings_query(conn, user_id)

def bulk_set_rankings(conn: Connection, user_id: int, rankings: List[Tuple[int, int]]) -> None:
    """rankings: list of (project_key, manual_rank)."""
    with _transaction_scope(conn):
        bulk_set_rankings_query(conn, user_id, rankings)

def set_project_rank(
    conn: Connection,
    user_id: int,
    project_key: int,
    manual_rank: Optional[int],
) -> None:
    """
    Set one project's manual rank with shifting behavior.

    This performs multiple writes (shifts + upsert), so it is executed atomically.
    """
    with _transaction_scope(conn):
        if manual_rank is None:
            clear_project_rank_query(conn, user_id, project_key)
            return

        current_rank = get_project_rank(conn, user_id, project_key)
        if current_rank == manual_rank:
            return

        if current_rank is None:
            shift_project_ranks_for_insert(conn, user_id, manual_rank)
        elif manual_rank < current_rank:
            shift_project_ranks_for_move_up(conn, user_id, manual_rank, current_rank, project_key)
        else:
            shift_project_ranks_for_move_down(conn, user_id, current_rank, manual_rank, project_key)

        upsert_project_rank(conn, user_id, project_key, manual_rank)