from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Tuple


# Keep statuses aligned with your CHECK constraint in tables.sql
UPLOAD_STATUSES = {
    "started",
    "parsed",
    "needs_classification",
    "needs_project_types",
    "needs_file_roles",
    "needs_summaries",
    "analyzing",
    "done",
    "failed",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_upload(
    conn: sqlite3.Connection,
    user_id: int,
    zip_name: Optional[str] = None,
    zip_path: Optional[str] = None,
    status: str = "started",
    state: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Create a new upload session row and return upload_id.
    """
    if status not in UPLOAD_STATUSES:
        raise ValueError(f"Invalid upload status: {status}")

    now = _utc_now_iso()
    state_json = json.dumps(state or {}, ensure_ascii=False)

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO uploads (user_id, zip_name, zip_path, status, state_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, zip_name, zip_path, status, state_json, now, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_upload_by_id(conn: sqlite3.Connection, upload_id: int) -> Optional[Dict[str, Any]]:
    """
    Return upload row as a dict, including parsed state_json, or None if not found.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT upload_id, user_id, zip_name, zip_path, status, state_json, created_at, updated_at
        FROM uploads
        WHERE upload_id = ?
        """,
        (upload_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    state = {}
    if row[5]:
        try:
            state = json.loads(row[5])
        except json.JSONDecodeError:
            state = {}

    return {
        "upload_id": row[0],
        "user_id": row[1],
        "zip_name": row[2],
        "zip_path": row[3],
        "status": row[4],
        "state": state,
        "created_at": row[6],
        "updated_at": row[7],
    }


def list_uploads_for_user(
    conn: sqlite3.Connection,
    user_id: int,
    limit: int = 25,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List recent uploads for a user (most recent first). Good for "resume upload" UX later.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT upload_id, user_id, zip_name, zip_path, status, state_json, created_at, updated_at
        FROM uploads
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset),
    )
    rows = cur.fetchall()

    out: List[Dict[str, Any]] = []
    for row in rows:
        state = {}
        if row[5]:
            try:
                state = json.loads(row[5])
            except json.JSONDecodeError:
                state = {}

        out.append(
            {
                "upload_id": row[0],
                "user_id": row[1],
                "zip_name": row[2],
                "zip_path": row[3],
                "status": row[4],
                "state": state,
                "created_at": row[6],
                "updated_at": row[7],
            }
        )
    return out


def update_upload_status(
    conn: sqlite3.Connection,
    upload_id: int,
    status: str,
) -> None:
    """
    Update only status.
    """
    if status not in UPLOAD_STATUSES:
        raise ValueError(f"Invalid upload status: {status}")

    now = _utc_now_iso()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE uploads
        SET status = ?, updated_at = ?
        WHERE upload_id = ?
        """,
        (status, now, upload_id),
    )
    conn.commit()


def update_upload_zip_metadata(
    conn: sqlite3.Connection,
    upload_id: int,
    zip_name: Optional[str] = None,
    zip_path: Optional[str] = None,
) -> None:
    """
    Update zip_name/zip_path (useful right after saving the uploaded file).
    Only updates fields that are not None.
    """
    sets = []
    params: List[Any] = []
    if zip_name is not None:
        sets.append("zip_name = ?")
        params.append(zip_name)
    if zip_path is not None:
        sets.append("zip_path = ?")
        params.append(zip_path)

    if not sets:
        return

    sets.append("updated_at = ?")
    params.append(_utc_now_iso())
    params.append(upload_id)

    cur = conn.cursor()
    cur.execute(
        f"""
        UPDATE uploads
        SET {", ".join(sets)}
        WHERE upload_id = ?
        """,
        tuple(params),
    )
    conn.commit()


def set_upload_state(
    conn: sqlite3.Connection,
    upload_id: int,
    state: Dict[str, Any],
    *,
    status: Optional[str] = None,
) -> None:
    """
    Replace state_json entirely. Optionally update status in the same write.
    """
    now = _utc_now_iso()
    state_json = json.dumps(state or {}, ensure_ascii=False)

    if status is not None and status not in UPLOAD_STATUSES:
        raise ValueError(f"Invalid upload status: {status}")

    if status is None:
        sql = """
            UPDATE uploads
            SET state_json = ?, updated_at = ?
            WHERE upload_id = ?
        """
        params = (state_json, now, upload_id)
    else:
        sql = """
            UPDATE uploads
            SET state_json = ?, status = ?, updated_at = ?
            WHERE upload_id = ?
        """
        params = (state_json, status, now, upload_id)

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()


def patch_upload_state(
    conn: sqlite3.Connection,
    upload_id: int,
    patch: Dict[str, Any],
    *,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Merge patch keys into existing state_json.
    Returns the new merged state.
    """
    current = get_upload_by_id(conn, upload_id)
    if current is None:
        raise ValueError(f"Upload not found: {upload_id}")

    state = current.get("state") or {}
    state.update(patch or {})
    set_upload_state(conn, upload_id, state, status=status)
    return state


def mark_upload_failed(
    conn: sqlite3.Connection,
    upload_id: int,
    error_message: str,
    *,
    error_code: Optional[str] = None,
) -> None:
    """
    Mark upload as failed and store error info in state_json.
    """
    patch = {
        "error": {
            "message": error_message,
            "code": error_code,
            "failed_at": _utc_now_iso(),
        }
    }
    patch_upload_state(conn, upload_id, patch, status="failed")


def delete_upload(conn: sqlite3.Connection, upload_id: int) -> None:
    """
    Optional: delete an upload row. Use carefully if you want resumability.
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM uploads WHERE upload_id = ?", (upload_id,))
    conn.commit()
