import sqlite3
from typing import List, Dict

def _fetch_files(conn: sqlite3.Connection, user_id: int, project_name: str, only_text: bool = False, only_code: bool = False) -> List[Dict[str, str]]:
    """
    Fetch files for a project from the 'files' table.
    Returns: [{'file_name','file_type','file_path'}, ...]
    """
    query = """
        SELECT file_name, file_type, file_path
        FROM files
        WHERE user_id = ? AND project_name = ?
    """
    params = [user_id, project_name]
    if only_text:
        query += " AND file_type = 'text'"
    elif only_code:
        query += " AND file_type = 'code'"

    rows = conn.execute(query, params).fetchall()
    return [{"file_name": r[0], "file_type": r[1], "file_path": r[2]} for r in rows]
