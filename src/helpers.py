import sqlite3
from typing import List, Dict, Optional
import os
import subprocess

def _fetch_files(conn: sqlite3.Connection, user_id: int, project_name: str, only_text: bool = False) -> List[Dict[str, str]]:
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

    rows = conn.execute(query, params).fetchall()
    return [{"file_name": r[0], "file_type": r[1], "file_path": r[2]} for r in rows]

import os
import sqlite3
from typing import Tuple, Optional, List

def zip_paths(zip_path: str) -> Tuple[str, str, str]:
    """
    Returns (zip_data_dir, zip_name, base_path)
    - zip_data_dir: absolute path to ./zip_data
    - zip_name:     the uploaded zip filename (no extension)
    - base_path:    ./zip_data/<zip_name>
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_data_dir = os.path.join(repo_root, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(zip_data_dir, zip_name)
    return zip_data_dir, zip_name, base_path

def ensure_table(conn: sqlite3.Connection, table: str, ddl: str) -> None:
    conn.execute(ddl)
    conn.commit()

def is_git_repo(path: str) -> bool:
    """
    A directory is a repo if it contains a .git FOLDER,
    or a .git FILE (worktree) pointing to another gitdir.
    """
    git_dir = os.path.join(path, ".git")
    if os.path.isdir(git_dir):
        return True
    if os.path.isfile(git_dir):
        try:
            with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                return "gitdir:" in f.read().lower()
        except Exception:
            return False
    return False

def bfs_find_repo(root: str, max_depth: int = 2) -> Optional[str]:
    """
    Breadth-first search to find a nested repo under root, up to max_depth.
    Returns the first directory containing .git.
    """
    if not os.path.isdir(root):
        return None
    if is_git_repo(root):
        return root
    queue: List[Tuple[str, int]] = [(root, 0)]
    while queue:
        path, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            entries = [os.path.join(path, ent) for ent in os.listdir(path)]
        except Exception:
            continue
        for p in entries:
            if os.path.isdir(p):
                if is_git_repo(p):
                    return p
                if depth < max_depth:
                    queue.append((p, depth + 1))
    return None
