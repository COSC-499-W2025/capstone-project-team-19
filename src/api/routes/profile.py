from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.user_profile import UserProfileDTO, UserProfileUpdateDTO
from src.db.user_profile import get_user_profile, upsert_user_profile

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

