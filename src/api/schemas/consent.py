from pydantic import BaseModel, Field
from typing import Literal


class ConsentRequestDTO(BaseModel):
    status: Literal["accepted", "rejected"] = Field(
        ...,
        description="User consent status - must be 'accepted' or 'rejected'"
    )

class ConsentResponseDTO(BaseModel):
    consent_id: int
    user_id: int
    status: str
    timestamp: str
