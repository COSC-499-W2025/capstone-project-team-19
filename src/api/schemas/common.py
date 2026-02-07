from pydantic import BaseModel
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

class ErrorDTO(BaseModel):
    message: str
    code: int

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDTO] = None


class DeleteResultDTO(BaseModel):
    deleted_count: int
