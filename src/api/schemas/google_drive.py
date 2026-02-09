from pydantic import BaseModel
from typing import List, Optional


class DriveStartRequest(BaseModel):
    connect_now: bool


class DriveStartResponse(BaseModel):
    auth_url: Optional[str] = None


class DriveFileDTO(BaseModel):
    id: str
    name: str
    mime_type: str


class DriveFilesResponse(BaseModel):
    files: List[DriveFileDTO]


class DriveLinkItem(BaseModel):
    local_file_name: str
    drive_file_id: str
    drive_file_name: str
    mime_type: str


class DriveLinkRequest(BaseModel):
    links: List[DriveLinkItem]
