from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlite3 import Connection
from typing import Literal

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.activity_heatmap import ActivityHeatmapInfoDTO, HeatmapMode
from src.services.activity_heatmap_service import (
    get_activity_heatmap_png_path,
    build_activity_heatmap_png_url,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_name}/activity-heatmap", response_model=ApiResponse[ActivityHeatmapInfoDTO])
def get_activity_heatmap_info(
    project_name: str,
    mode: HeatmapMode = Query("diff"),
    normalize: bool = Query(True),
    include_unclassified_text: bool = Query(True),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        # Generate (or reuse cached) artifact, but return a friendly URL for clients.
        _path = get_activity_heatmap_png_path(
            conn,
            user_id,
            project_name,
            mode=mode,
            normalize=normalize,
            include_unclassified_text=include_unclassified_text,
        )
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Project not found")
        if "no versions" in msg:
            raise HTTPException(status_code=400, detail="Project has no versions")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

    dto = ActivityHeatmapInfoDTO(
        project_name=project_name,
        mode=mode,
        normalize=normalize,
        include_unclassified_text=include_unclassified_text,
        png_url=build_activity_heatmap_png_url(project_name, mode, normalize, include_unclassified_text),
    )
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/{project_name}/activity-heatmap.png")
def get_activity_heatmap_png(
    project_name: str,
    mode: HeatmapMode = Query("diff"),
    normalize: bool = Query(True),
    include_unclassified_text: bool = Query(True),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        path = get_activity_heatmap_png_path(
            conn,
            user_id,
            project_name,
            mode=mode,
            normalize=normalize,
            include_unclassified_text=include_unclassified_text,
        )
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Project not found")
        if "no versions" in msg:
            raise HTTPException(status_code=400, detail="Project has no versions")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

    return FileResponse(path, media_type="image/png")