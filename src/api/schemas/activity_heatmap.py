from pydantic import BaseModel
from typing import Literal

HeatmapMode = Literal["diff", "snapshot"]


class ActivityHeatmapInfoDTO(BaseModel):
    project_name: str
    mode: HeatmapMode = "diff"
    normalize: bool = True
    include_unclassified_text: bool = True
    png_url: str