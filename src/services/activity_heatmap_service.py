from sqlite3 import Connection
from typing import Literal, Tuple

from src.db.projects import get_project_key
from src.analysis.visualizations.activity_heatmap import write_project_activity_heatmap

HeatmapMode = Literal["diff", "snapshot"]


def _resolve_project_name_from_project_id(
    conn: Connection,
    user_id: int,
    project_id: int,
) -> str | None:
    row = conn.execute(
        """
        SELECT project_name
        FROM project_summaries
        WHERE user_id = ? AND project_summary_id = ?
        LIMIT 1
        """,
        (user_id, project_id),
    ).fetchone()
    return row[0] if row and row[0] else None


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