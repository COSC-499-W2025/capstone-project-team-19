from sqlite3 import Connection
from typing import Literal

from src.db.projects import get_project_key
from src.analysis.visualizations.activity_heatmap import write_project_activity_heatmap

HeatmapMode = Literal["diff", "snapshot"]


def get_activity_heatmap_png_path(
    conn: Connection,
    user_id: int,
    project_name: str,
    mode: HeatmapMode = "diff",
    normalize: bool = True,
    include_unclassified_text: bool = True,
) -> str:
    # Distinguish "project doesn't exist" vs "no versions"
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        raise ValueError("Project not found")

    return write_project_activity_heatmap(
        conn,
        user_id,
        project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
    )


def build_activity_heatmap_png_url(
    project_name: str,
    mode: HeatmapMode,
    normalize: bool,
    include_unclassified_text: bool,
) -> str:
    # Just a convenient URL for clients.
    # FastAPI will handle URL encoding for project_name in the path.
    return (
        f"/projects/{project_name}/activity-heatmap.png"
        f"?mode={mode}"
        f"&normalize={'true' if normalize else 'false'}"
        f"&include_unclassified_text={'true' if include_unclassified_text else 'false'}"
    )