from pydantic import BaseModel
from typing import List, Literal

HeatmapMode = Literal["diff", "snapshot"]


class ActivityHeatmapInfoDTO(BaseModel):
    project_id: int
    project_name: str
    mode: HeatmapMode = "diff"
    normalize: bool = True
    include_unclassified_text: bool = True
    png_url: str


class ActivityHeatmapDataDTO(BaseModel):
    project_id: int
    project_name: str
    mode: HeatmapMode = "diff"
    normalize: bool = True
    include_unclassified_text: bool = True
    matrix: List[List[float]]
    row_labels: List[str]
    col_labels: List[str]
    title: str