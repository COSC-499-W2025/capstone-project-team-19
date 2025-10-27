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

# ---------------------------------------------------------------------------
# New shared helpers for Git + path operations
# ---------------------------------------------------------------------------

def resolve_zip_base(zip_path: str) -> str:
    """Return the extracted folder path under repo_root/zip_data/<zip_name>."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_data_dir = os.path.join(repo_root, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    return os.path.join(zip_data_dir, zip_name)


def find_project_dir(base_path: str, project_name: str) -> Optional[str]:
    """Try common layouts for extracted projects; return first that exists."""
    candidates = [
        os.path.join(base_path, project_name),
        os.path.join(base_path, "collaborative", project_name),
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return None


def is_git_repo(path: str) -> bool:
    """Detect .git directory or indirection file."""
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


def run_git(repo_dir: str, args: List[str]) -> str:
    """Run a git command and return stdout (utf-8)."""
    cmd = ["git", "-C", repo_dir] + args
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="replace")
        print(f"[git error] {' '.join(cmd)}\n{msg}")
        return ""


def file_ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def top_folder(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    return parts[0] if parts else ""


def ext_to_lang(ext: str) -> str:
    """Map common extensions to languages for summary output."""
    m = {
        ".py": "Python", ".ipynb": "Jupyter", ".js": "JS", ".ts": "TS",
        ".tsx": "TSX", ".jsx": "JSX", ".java": "Java", ".cs": "C#",
        ".cpp": "C++", ".cxx": "C++", ".cc": "C++", ".c": "C",
        ".rs": "Rust", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
        ".kt": "Kotlin", ".swift": "Swift", ".m": "Obj-C",
        ".h": "Header", ".hpp": "Header", ".hh": "Header",
        ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML",
        ".sh": "Shell", ".ps1": "Powershell",
    }
    return m.get(ext, ext.replace(".", "").upper() or "Other")