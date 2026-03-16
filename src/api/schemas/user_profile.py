from typing import Optional

from pydantic import BaseModel


class UserProfileDTO(BaseModel):
    user_id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    profile_text: Optional[str] = None


class UserProfileUpdateDTO(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    profile_text: Optional[str] = None

