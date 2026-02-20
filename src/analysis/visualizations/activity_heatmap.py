"""
Generate a PNG heatmap of activity type vs project version.

X axis = versions (oldest -> newest)
Y axis = activity types (code or text)
Cell value = % (default) or raw counts

Modes:
- mode='snapshot': classify all files present in each version
- mode='diff': classify only files touched in that version
  (added + modified vs previous version; v1 uses all files)
"""

from __future__ import annotations

import io
import os
import re
import sqlite3
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

from src.db.projects import get_project_key
from src.db.version_evolution import (
    get_file_diff_between_versions,
    get_version_keys_ordered_for_project,
)

from src.analysis.activity_type.code.rules import infer_activity_from_filename
from src.analysis.activity_type.code.types import ActivityType as CodeActivityType

from src.analysis.activity_type.text.activity_type import (
    ACTIVITY_TYPES as TEXT_ACTIVITY_TYPES,
    detect_activity_type as detect_text_activity,
)

HeatmapMode = Literal["snapshot", "diff"]

EXCLUDE_DIRS_DEFAULT = {
    "node_modules", ".venv", "venv", "__pycache__", ".git", ".idea", ".vscode",
    "dist", "build", "target", "out",
}

CODE_EXTS = {
    ".py", ".java", ".js", ".jsx", ".ts", ".tsx",
    ".c", ".h", ".cpp", ".hpp",
    ".go", ".rs", ".cs", ".kt", ".swift",
    ".php", ".rb", ".scala", ".sql",
    ".html", ".css",
    ".md", ".rst",
}

TEXT_EXTS = {
    ".doc", ".docx", ".pdf", ".txt", ".md", ".rtf", ".odt", ".tex",
    ".csv", ".xls", ".xlsx",
}


def _safe_slug(s: str) -> str:
    s = (s or "project").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "_", s)
    return s.strip("_") or "project"


def _basename(path: str) -> str:
    path = (path or "").replace("\\", "/")
    return path.split("/")[-1]


def _ext(path: str) -> str:
    base = _basename(path)
    _, e = os.path.splitext(base)
    return e.lower()


def _is_excluded_path(path: str, exclude_dirs: set[str]) -> bool:
    p = (path or "").replace("\\", "/")
    for d in exclude_dirs:
        if f"/{d}/" in f"/{p}/":
            return True
    return False


def _pick_final_code_activity(scores: Dict[CodeActivityType, int]) -> CodeActivityType:
    """Mirror labeler.py tie-breaking priority."""
    priority = [
        CodeActivityType.TESTING,
        CodeActivityType.DOCUMENTATION,
        CodeActivityType.DEBUGGING,
        CodeActivityType.REFACTORING,
        CodeActivityType.FEATURE_CODING,
    ]

    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return CodeActivityType.FEATURE_CODING

    candidates = [at for at, s in scores.items() if s == max_score]
    for at in priority:
        if at in candidates:
            return at

    return CodeActivityType.FEATURE_CODING


def _code_activity_rows() -> List[str]:
    return [
        CodeActivityType.FEATURE_CODING.value,
        CodeActivityType.REFACTORING.value,
        CodeActivityType.DEBUGGING.value,
        CodeActivityType.TESTING.value,
        CodeActivityType.DOCUMENTATION.value,
    ]


def _text_activity_rows(include_unclassified: bool = True) -> List[str]:
    rows = [a.name for a in sorted(TEXT_ACTIVITY_TYPES, key=lambda x: x.priority)]
    if include_unclassified:
        rows.append("Unclassified")
    return rows


def _pretty_label(activity_key: str) -> str:
    return activity_key.replace("_", " ").title()


def _get_project_type(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[str]:
    row = conn.execute(
        """
        SELECT project_type
        FROM projects
        WHERE user_id = ? AND display_name = ?
        ORDER BY project_key DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row and row[0] else None


def _get_relpaths_for_version(conn: sqlite3.Connection, version_key: int) -> List[str]:
    rows = conn.execute(
        "SELECT relpath FROM version_files WHERE version_key = ?",
        (int(version_key),),
    ).fetchall()
    return [str(r[0]) for r in rows or [] if r and r[0]]


def _relpaths_for_version_mode(
    conn: sqlite3.Connection,
    version_keys_ordered: Sequence[int],
    idx: int,
    mode: HeatmapMode,
) -> List[str]:
    vk = int(version_keys_ordered[idx])

    if mode == "snapshot":
        return _get_relpaths_for_version(conn, vk)

    # mode == "diff"
    if idx == 0:
        return _get_relpaths_for_version(conn, vk)

    prev_vk = int(version_keys_ordered[idx - 1])
    diff = get_file_diff_between_versions(conn, prev_vk, vk)
    touched = list(diff.get("added", [])) + list(diff.get("modified", []))
    return [str(p) for p in touched if p]


def _filter_paths_for_project_type(paths: Iterable[str], project_type: str, exclude_dirs: set[str]) -> List[str]:
    out: List[str] = []
    for p in paths:
        if not p:
            continue
        if _is_excluded_path(p, exclude_dirs):
            continue
        e = _ext(p)

        if project_type == "code":
            if e and e in CODE_EXTS:
                out.append(p)
        else:
            if e and e in TEXT_EXTS:
                out.append(p)

    return out


def _count_code_activities(relpaths: Sequence[str]) -> Dict[str, int]:
    counts = {k: 0 for k in _code_activity_rows()}

    for p in relpaths:
        name = _basename(p)
        scores = infer_activity_from_filename(name, p)
        at = _pick_final_code_activity(scores)
        counts[at.value] = counts.get(at.value, 0) + 1

    return counts


def _count_text_activities(relpaths: Sequence[str], include_unclassified: bool = True) -> Dict[str, int]:
    rows = _text_activity_rows(include_unclassified=include_unclassified)
    counts = {k: 0 for k in rows}

    for p in relpaths:
        name = _basename(p)
        at = detect_text_activity(name) or ("Unclassified" if include_unclassified else None)
        if at is None:
            continue
        if at not in counts:
            counts[at] = 0
        counts[at] += 1

    return counts


def _counts_to_vector(counts: Dict[str, int], row_keys: Sequence[str], normalize: bool) -> List[float]:
    total = sum(int(v or 0) for v in counts.values())
    vec: List[float] = []
    for k in row_keys:
        c = float(counts.get(k, 0) or 0)
        vec.append((c / total * 100.0) if (normalize and total > 0) else (c if not normalize else 0.0))
    return vec


def build_project_activity_heatmap_matrix(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    *,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
    exclude_dirs: Optional[set[str]] = None,
) -> Tuple[np.ndarray, List[str], List[str], str]:
    project_type = _get_project_type(conn, user_id, project_name)
    if project_type not in {"code", "text"}:
        raise ValueError(f"Project '{project_name}' has unknown project_type={project_type!r}")

    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        raise ValueError(f"Project '{project_name}' not found for user_id={user_id}")

    exclude_dirs = exclude_dirs or set(EXCLUDE_DIRS_DEFAULT)

    version_pairs = get_version_keys_ordered_for_project(conn, int(project_key))
    version_keys = [vk for vk, _created_at in version_pairs]
    if not version_keys:
        raise ValueError(f"Project '{project_name}' has no versions")

    col_labels = [f"v{i+1}" for i in range(len(version_keys))]

    row_keys = _code_activity_rows() if project_type == "code" else _text_activity_rows(include_unclassified=include_unclassified_text)

    vectors: List[List[float]] = []
    for i in range(len(version_keys)):
        relpaths_raw = _relpaths_for_version_mode(conn, version_keys, i, mode)
        relpaths = _filter_paths_for_project_type(relpaths_raw, project_type, exclude_dirs)

        counts = _count_code_activities(relpaths) if project_type == "code" else _count_text_activities(relpaths, include_unclassified=include_unclassified_text)
        vectors.append(_counts_to_vector(counts, row_keys, normalize=normalize))

    mat = np.array(vectors, dtype=float).T  # rows x cols
    y_labels = [_pretty_label(k) for k in row_keys]

    value_label = "%" if normalize else "count"
    title = f"{project_name} • Activity vs Version ({mode}, {value_label})"
    return mat, y_labels, col_labels, title


def render_heatmap_png(
    matrix: np.ndarray,
    row_labels: Sequence[str],
    col_labels: Sequence[str],
    title: str,
    *,
    dpi: int = 180,
) -> bytes:
    n_rows, n_cols = matrix.shape
    fig_w = max(6.0, min(18.0, 0.55 * n_cols + 2.5))
    fig_h = max(4.0, min(12.0, 0.45 * n_rows + 2.0))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    im = ax.imshow(matrix, aspect="auto")

    ax.set_title(title)

    ax.set_xticks(np.arange(n_cols))
    ax.set_xticklabels(list(col_labels), rotation=45, ha="right")

    ax.set_yticks(np.arange(n_rows))
    ax.set_yticklabels(list(row_labels))

    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    ax.grid(which="minor", linestyle="-", linewidth=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


def build_project_activity_heatmap_png(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    *,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
) -> bytes:
    mat, y, x, title = build_project_activity_heatmap_matrix(
        conn,
        user_id,
        project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
    )
    return render_heatmap_png(mat, y, x, title)


def write_project_activity_heatmap(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    *,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
    out_dir: Optional[str] = None,
) -> str:
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        raise ValueError(f"Project '{project_name}' not found")

    version_pairs = get_version_keys_ordered_for_project(conn, int(project_key))
    latest_vk = version_pairs[-1][0] if version_pairs else 0

    base_dir = out_dir or os.path.join("data", "artifacts", "heatmaps")
    os.makedirs(base_dir, exist_ok=True)

    fname = f"u{user_id}_p{project_key}_{_safe_slug(project_name)}_{mode}_vk{latest_vk}.png"
    out_path = os.path.join(base_dir, fname)

    # cache: versioned filename means safe reuse
    if os.path.exists(out_path):
        return out_path

    png = build_project_activity_heatmap_png(
        conn,
        user_id,
        project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
    )
    with open(out_path, "wb") as f:
        f.write(png)

    return out_path