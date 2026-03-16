from sqlite3 import Connection
from typing import Any, Dict, Literal, Tuple

from src.db.project_summaries import get_project_summary_by_id
from src.db.projects import get_project_key
from src.analysis.visualizations.activity_heatmap import (
    write_project_activity_heatmap,
    build_project_activity_heatmap_matrix,
)

HeatmapMode = Literal["diff", "snapshot"]


def _resolve_project_name_from_project_id(
    conn: Connection,
    user_id: int,
    project_id: int,
) -> str | None:
    row = get_project_summary_by_id(conn, user_id, project_id)
    return row.get("project_name") if row else None


def get_activity_heatmap_png_path(
    conn: Connection,
    user_id: int,
    project_id: int,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
) -> Tuple[str, str]:
    project_name = _resolve_project_name_from_project_id(conn, user_id, project_id)
    if project_name is None:
        raise ValueError("Project not found")

    # Distinguish "project doesn't exist" vs "no versions"
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        # In case project_summaries exists but projects row is missing
        raise ValueError("Project not found")

    path = write_project_activity_heatmap(
        conn,
        user_id,
        project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
    )
    return project_name, path


def build_activity_heatmap_png_url(
    project_id: int,
    mode: HeatmapMode,
    normalize: bool,
    include_unclassified_text: bool,
) -> str:
    return (
        f"/projects/{project_id}/activity-heatmap.png"
        f"?mode={mode}"
        f"&normalize={'true' if normalize else 'false'}"
        f"&include_unclassified_text={'true' if include_unclassified_text else 'false'}"
    )


def get_activity_heatmap_data(
    conn: Connection,
    user_id: int,
    project_id: int,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
) -> Dict[str, Any]:
    project_name = _resolve_project_name_from_project_id(conn, user_id, project_id)
    if project_name is None:
        raise ValueError("Project not found")

    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        raise ValueError("Project not found")

    mat, row_labels, col_labels, title = build_project_activity_heatmap_matrix(
        conn,
        user_id,
        project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
    )
    return {
        "project_id": project_id,
        "project_name": project_name,
        "mode": mode,
        "normalize": normalize,
        "include_unclassified_text": include_unclassified_text,
        "matrix": mat.tolist(),
        "row_labels": list(row_labels),
        "col_labels": list(col_labels),
        "title": title,
    }