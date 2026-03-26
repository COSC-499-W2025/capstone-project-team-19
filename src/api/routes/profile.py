from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.user_profile import (
    UserProfileDTO,
    UserProfileUpdateDTO,
    UserEducationEntryDTO,
    UserEducationListDTO,
    UserEducationEntriesUpdateDTO,
    UserExperienceEntryDTO,
    UserExperienceListDTO,
    UserExperienceEntriesUpdateDTO,
)
from src.db.user_profile import get_user_profile, upsert_user_profile
from src.db.user_education import list_user_education_entries, add_user_education_entry
from src.db.user_experience import (
    list_user_experience_entries,
    add_user_experience_entry,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ApiResponse[UserProfileDTO])
def get_profile(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    profile = get_user_profile(conn, user_id)
    dto = UserProfileDTO(**profile)
    return ApiResponse(success=True, data=dto, error=None)


@router.put("", response_model=ApiResponse[UserProfileDTO])
def put_profile(
    request: UserProfileUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    current = get_user_profile(conn, user_id)

    email = request.email if request.email is not None else current.get("email")
    full_name = request.full_name if request.full_name is not None else current.get("full_name")
    phone = request.phone if request.phone is not None else current.get("phone")
    linkedin = request.linkedin if request.linkedin is not None else current.get("linkedin")
    github = request.github if request.github is not None else current.get("github")
    location = request.location if request.location is not None else current.get("location")
    profile_text = request.profile_text if request.profile_text is not None else current.get("profile_text")

    try:
        upsert_user_profile(
            conn,
            user_id,
            email=email,
            full_name=full_name,
            phone=phone,
            linkedin=linkedin,
            github=github,
            location=location,
            profile_text=profile_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated = get_user_profile(conn, user_id)
    dto = UserProfileDTO(**updated)
    return ApiResponse(success=True, data=dto, error=None)


def _map_education_entries(entries, *, entry_type: str) -> UserEducationListDTO:
    filtered = [e for e in entries if e.get("entry_type") == entry_type]
    return UserEducationListDTO(
        entries=[UserEducationEntryDTO(**entry) for entry in filtered]
    )


@router.get("/education", response_model=ApiResponse[UserEducationListDTO])
def get_education(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    entries = list_user_education_entries(conn, user_id)
    dto = _map_education_entries(entries, entry_type="education")
    return ApiResponse(success=True, data=dto, error=None)


@router.put("/education", response_model=ApiResponse[UserEducationListDTO])
def put_education(
    request: UserEducationEntriesUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        conn.execute(
            "DELETE FROM user_education_entries WHERE user_id = ? AND entry_type = 'education'",
            (user_id,),
        )
        conn.commit()

        for entry in request.entries:
            add_user_education_entry(
                conn,
                user_id,
                entry_type="education",
                title=entry.title,
                organization=entry.organization,
                date_text=entry.date_text,
                description=entry.description,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    entries = list_user_education_entries(conn, user_id)
    dto = _map_education_entries(entries, entry_type="education")
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/certifications", response_model=ApiResponse[UserEducationListDTO])
def get_certifications(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    entries = list_user_education_entries(conn, user_id)
    dto = _map_education_entries(entries, entry_type="certificate")
    return ApiResponse(success=True, data=dto, error=None)


@router.get("/experience", response_model=ApiResponse[UserExperienceListDTO])
def get_experience(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    entries = list_user_experience_entries(conn, user_id)
    return ApiResponse(
        success=True,
        data=UserExperienceListDTO(
            entries=[UserExperienceEntryDTO(**entry) for entry in entries]
        ),
        error=None,
    )


@router.put("/experience", response_model=ApiResponse[UserExperienceListDTO])
def put_experience(
    request: UserExperienceEntriesUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        conn.execute(
            "DELETE FROM user_experience_entries WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

        for entry in request.entries:
            add_user_experience_entry(
                conn,
                user_id,
                role=entry.role,
                company=entry.company,
                date_text=entry.date_text,
                description=entry.description,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    entries = list_user_experience_entries(conn, user_id)
    return ApiResponse(
        success=True,
        data=UserExperienceListDTO(
            entries=[UserExperienceEntryDTO(**entry) for entry in entries]
        ),
        error=None,
    )


@router.put("/certifications", response_model=ApiResponse[UserEducationListDTO])
def put_certifications(
    request: UserEducationEntriesUpdateDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    try:
        conn.execute(
            "DELETE FROM user_education_entries WHERE user_id = ? AND entry_type = 'certificate'",
            (user_id,),
        )
        conn.commit()

        for entry in request.entries:
            add_user_education_entry(
                conn,
                user_id,
                entry_type="certificate",
                title=entry.title,
                organization=entry.organization,
                date_text=entry.date_text,
                description=entry.description,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    entries = list_user_education_entries(conn, user_id)
    dto = _map_education_entries(entries, entry_type="certificate")
    return ApiResponse(success=True, data=dto, error=None)

