from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Tuple


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

    norm = PurePosixPath(*[part for part in p.parts if part not in ("", ".")])
    return norm.as_posix()


def compute_relpath_for_api(zip_data_dir: Path, file_path: str, project_name: str | None) -> str:
    """
    Best-effort: returns a stable POSIX relpath for UI/API.

    Handles:
    - absolute paths under ZIP_DATA_DIR -> strip to ZIP_DATA_DIR-relative
    - already-relative paths -> normalize
    - absolute paths outside ZIP_DATA_DIR -> fallback to start at project folder or filename
    """
    raw = str(file_path or "")
    if not raw:
        return ""

    # If it's already relative, just normalize
    p = Path(raw)
    if not p.is_absolute():
        return PurePosixPath(raw.replace("\\", "/")).as_posix()

    base = Path(zip_data_dir).resolve()
    try:
        rel = p.resolve().relative_to(base)
        return PurePosixPath(rel).as_posix()
    except Exception:
        posix = PurePosixPath(p.as_posix())
        if project_name and project_name in posix.parts:
            i = posix.parts.index(project_name)
            return PurePosixPath(*posix.parts[i:]).as_posix()
        return PurePosixPath(p.name).as_posix()


def build_file_item_from_row(zip_data_dir: Path, row: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Expected row shape:
    (file_name, file_path, extension, file_type, size_bytes, created, modified, project_name)
    """
    file_name, file_path, ext, file_type, size_bytes, created, modified, project_name = row

    relpath = compute_relpath_for_api(zip_data_dir, str(file_path), project_name)

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
    all_files = list(items)

    text_files = [f for f in items if (f.get("file_type") == "text")]
    csv_files = [
        f
        for f in items
        if (str(f.get("extension") or "").lower() == ".csv")
        or (str(f.get("file_name") or "").lower().endswith(".csv"))
    ]

    return {
        "all_files": all_files,
        "text_files": text_files,
        "csv_files": csv_files,
    }