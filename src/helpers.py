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
    """
    Find a project directory under the extracted upload base.

    Supports these layouts:
      zip_data/<zip_name>/<project_name>
      zip_data/<zip_name>/collaborative/<project_name>
      zip_data/<zip_name>/<root_folder>/<project_name>
      zip_data/<zip_name>/<root_folder>/collaborative/<project_name>
    """
    # 1) Direct candidates (no extra root folder)
    direct = [
        os.path.join(base_path, project_name),
        os.path.join(base_path, "collaborative", project_name),
    ]
    for p in direct:
        if os.path.isdir(p):
            return p

    # 2) With a single root folder between zip_name and project
    try:
        for root in os.listdir(base_path):
            root_path = os.path.join(base_path, root)
            if not os.path.isdir(root_path):
                continue
            cand = [
                os.path.join(root_path, project_name),
                os.path.join(root_path, "collaborative", project_name),
            ]
            for p in cand:
                if os.path.isdir(p):
                    return p
    except FileNotFoundError:
        pass

    # 3) As a last resort, do a shallow walk (depth <= 3) looking for the exact folder name
    max_depth = base_path.rstrip(os.sep).count(os.sep) + 3
    for cur, dirs, _files in os.walk(base_path):
        # stop walking too deep
        if cur.count(os.sep) > max_depth:
            continue
        for d in dirs:
            if d == project_name:
                candidate = os.path.join(cur, d)
                if os.path.isdir(candidate):
                    return candidate

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