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
from src.utils.parsing import CODE_EXTENSIONS as PARSING_CODE_EXTENSIONS
from src.utils.parsing import TEXT_EXTENSIONS as PARSING_TEXT_EXTENSIONS

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

from src.db import (
    get_project_key,
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

# these are common "ignore" directories that would add noise to the activity classification and are not relevant to the analysis
EXCLUDE_DIRS_DEFAULT = {
    "node_modules", ".venv", "venv", "__pycache__", ".git", ".idea", ".vscode",
    "dist", "build", "target", "out",
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
            if e and e in PARSING_CODE_EXTENSIONS:
                out.append(p)
        else:
            if e and e in PARSING_TEXT_EXTENSIONS:
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
    row_labels,
    col_labels,
    title: str,
    *,
    dpi: int = 180,
) -> bytes:
    n_rows, n_cols = matrix.shape

    # --- GitHub light theme palette (0 + 4 greens) ---
    github_colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    cmap = ListedColormap(github_colors)

    data = np.array(matrix, dtype=float)

    # Build bucket boundaries (0 is its own bucket, rest based on quantiles of non-zero values)
    nz = data[data > 0]
    if nz.size == 0:
        bounds = [0.0, 1e-9, 1.0, 2.0, 3.0, 4.0]  # arbitrary; everything will map to 0 anyway
    else:
        q = np.quantile(nz, [0.25, 0.50, 0.75, 0.90])
        bounds = [0.0, 1e-9, float(q[0]), float(q[1]), float(q[2]), float(nz.max()) + 1e-9]

        # Ensure strictly increasing bounds (avoid edge cases when values are uniform)
        for i in range(2, len(bounds)):
            if bounds[i] <= bounds[i - 1]:
                bounds[i] = bounds[i - 1] + 1e-9

    norm = BoundaryNorm(bounds, cmap.N, clip=True)

    # Size tuned for tiles
    fig_w = max(6.0, min(18.0, 0.60 * n_cols + 2.5))
    fig_h = max(4.0, min(12.0, 0.55 * n_rows + 2.0))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    # Draw tiles with "gaps"
    x = np.arange(n_cols + 1)
    y = np.arange(n_rows + 1)
    ax.pcolormesh(
        x, y, data,
        cmap=cmap,
        norm=norm,
        edgecolors="white",
        linewidth=1.0,
        antialiased=True,
    )
    ax.invert_yaxis()              # top row at top
    ax.set_aspect("auto")

    ax.set_title(title)

    # Center tick labels in each tile
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_xticklabels(list(col_labels), rotation=45, ha="right")
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_yticklabels(list(row_labels))

    # GitHub-ish minimal axes
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Small "Less → More" legend (like GitHub)
    legend_items = [
        Patch(facecolor=github_colors[0], edgecolor="none", label="Less"),
        Patch(facecolor=github_colors[1], edgecolor="none", label=""),
        Patch(facecolor=github_colors[2], edgecolor="none", label=""),
        Patch(facecolor=github_colors[3], edgecolor="none", label=""),
        Patch(facecolor=github_colors[4], edgecolor="none", label="More"),
    ]
    ax.legend(
        handles=legend_items,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.16),
        ncol=5,
        frameon=False,
        handlelength=1.0,
        handleheight=1.0,
        columnspacing=0.8,
        borderaxespad=0.0,
    )

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