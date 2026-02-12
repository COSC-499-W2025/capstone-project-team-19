from pydantic import BaseModel


class ThumbnailUploadDTO(BaseModel):
    project_id: int
    project_name: str
    message: str
