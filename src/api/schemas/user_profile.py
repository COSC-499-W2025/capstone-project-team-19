from typing import List, Optional

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


class UserEducationEntryDTO(BaseModel):
    entry_id: int
    entry_type: str
    title: str
    organization: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None
    display_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserEducationListDTO(BaseModel):
    entries: List[UserEducationEntryDTO]


class UserEducationEntryInputDTO(BaseModel):
    title: str
    organization: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None


class UserEducationEntriesUpdateDTO(BaseModel):
    entries: List[UserEducationEntryInputDTO]


class UserExperienceEntryDTO(BaseModel):
    entry_id: int
    role: str
    company: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None
    display_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserExperienceListDTO(BaseModel):
    entries: List[UserExperienceEntryDTO]


class UserExperienceEntryInputDTO(BaseModel):
    role: str
    company: Optional[str] = None
    date_text: Optional[str] = None
    description: Optional[str] = None


class UserExperienceEntriesUpdateDTO(BaseModel):
    entries: List[UserExperienceEntryInputDTO]

