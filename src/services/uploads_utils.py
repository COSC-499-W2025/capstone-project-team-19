from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
from typing import Any, Dict, Iterable, List, Set, Tuple


ALLOWED_CLASSIFICATIONS: Set[str] = {"individual", "collaborative"}
ALLOWED_PROJECT_TYPES: Set[str] = {"code", "text"}


def safe_zip_filename(name: str) -> str:
    """
    Sanitize a filename coming from UploadFile.filename.
    Keeps only alnum + . _ -
    """
    name = (name or "").strip()
    name = name.split("/")[-1].split("\\")[-1]
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "upload.zip"


def get_layout_known_projects(state: Dict[str, Any]) -> Set[str]:
    """
    Returns all detected project names from uploads.state_json.layout.
    """
    layout = (state or {}).get("layout") or {}
    pending = set(layout.get("pending_projects") or [])
    auto = set((layout.get("auto_assignments") or {}).keys())
    return pending | auto


def validate_classification_values(assignments: Dict[str, str]) -> Dict[str, str]:
    """
    Returns invalid values dict {project: bad_value}.
    """
    return {k: v for k, v in (assignments or {}).items() if v not in ALLOWED_CLASSIFICATIONS}


def validate_project_type_values(project_types: Dict[str, str]) -> Dict[str, str]:
    """
    Returns invalid values dict {project: bad_value}.
    """
    return {k: v for k, v in (project_types or {}).items() if v not in ALLOWED_PROJECT_TYPES}


def unknown_assignment_keys(assignments: Dict[str, str], known_projects: Set[str]) -> List[str]:
    """
    Returns list of assignment keys not in known_projects.
    """
    return [p for p in (assignments or {}).keys() if p not in known_projects]


def safe_relpath(relpath: str) -> str:
    """
    Validates a client-provided relpath:
    - must be relative
    - must not contain '..'
    - normalizes to posix string
    """
    if not relpath or not isinstance(relpath, str):
        raise ValueError("relpath is required")

    p = PurePosixPath(relpath.strip())

    if str(p).startswith("/") or p.is_absolute():
        raise ValueError("relpath must be relative")

    if any(part == ".." for part in p.parts):
        raise ValueError("relpath must not contain '..'")

    # normalize: collapse "." etc.
    norm = PurePosixPath(*[part for part in p.parts if part not in ("", ".")])
    return norm.as_posix()


def compute_relpath_under_zip_data(zip_data_dir: Path, file_path: str) -> str:
    """
    Convert an absolute extracted file path into a POSIX relpath under ZIP_DATA_DIR.
    Example:
      ZIP_DATA_DIR=/.../src/analysis/zip_data
      file_path=/.../src/analysis/zip_data/myzip/ProjA/docs/report.docx
      -> myzip/ProjA/docs/report.docx
    """
    base = Path(zip_data_dir).resolve()
    p = Path(file_path).resolve()
    rel = p.relative_to(base)  # raises ValueError if p not under base
    return PurePosixPath(rel).as_posix()


def build_file_item_from_row(zip_data_dir: Path, row: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Expected row shape (from files table):
    (file_name, file_path, extension, file_type, size_bytes, created, modified, project_name)
    """
    file_name, file_path, ext, file_type, size_bytes, created, modified, project_name = row

    relpath = compute_relpath_under_zip_data(zip_data_dir, str(file_path))

    return {
        "file_name": file_name,
        "relpath": relpath,
        "extension": ext,
        "file_type": file_type,
        "size_bytes": size_bytes,
        "created": created,
        "modified": modified,
        "project_name": project_name,
    }


def categorize_project_files(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns:
      - all_files: everything for project
      - text_files: file_type == "text"
      - csv_files: extension == ".csv" (or file_name endswith .csv)
    """
    all_files = list(items)

    text_files = [f for f in items if (f.get("file_type") == "text")]
    csv_files = [
        f for f in items
        if (str(f.get("extension") or "").lower() == ".csv")
        or (str(f.get("file_name") or "").lower().endswith(".csv"))
    ]

    return {
        "all_files": all_files,
        "text_files": text_files,
        "csv_files": csv_files,
    }
