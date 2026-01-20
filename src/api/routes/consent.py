from fastapi import APIRouter, Depends
from sqlite3 import Connection
from datetime import datetime

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.consent import ConsentRequestDTO, ConsentResponseDTO, ConsentStatusDTO
from src.consent.consent import record_consent
from src.consent.external_consent import record_external_consent
from src.db import get_latest_consent, get_latest_external_consent

router = APIRouter(prefix="/privacy-consent", tags=["consent"])


@router.post("/internal", response_model=ApiResponse[ConsentResponseDTO], status_code=201)
def record_internal_consent_endpoint(
    request: ConsentRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """
    Record internal processing consent for the authenticated user.

    The user's consent status is recorded in the database with a timestamp.
    """
    # Record consent using existing function
    consent_id = record_consent(conn, request.status, user_id)

    # Get the timestamp that was just recorded
    timestamp = datetime.now().isoformat()

    # Build response DTO
    response_dto = ConsentResponseDTO(
        consent_id=consent_id,
        user_id=user_id,
        status=request.status,
        timestamp=timestamp
    )

    return ApiResponse(success=True, data=response_dto, error=None)


@router.post("/external", response_model=ApiResponse[ConsentResponseDTO], status_code=201)
def record_external_consent_endpoint(
    request: ConsentRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """
    Record external integration consent for the authenticated user.

    The user's consent status for external services is recorded in the database with a timestamp.
    """
    # Record consent using existing function
    consent_id = record_external_consent(conn, request.status, user_id)

    # Get the timestamp that was just recorded
    timestamp = datetime.now().isoformat()

    # Build response DTO
    response_dto = ConsentResponseDTO(
        consent_id=consent_id,
        user_id=user_id,
        status=request.status,
        timestamp=timestamp
    )

    return ApiResponse(success=True, data=response_dto, error=None)

@router.get("/status", response_model=ApiResponse[ConsentStatusDTO])
def get_consent_status(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    internal_consent = get_latest_consent(conn, user_id)
    external_consent = get_latest_external_consent(conn, user_id)

    status_dto = ConsentStatusDTO(
        user_id=user_id,
        internal_consent=internal_consent,
        external_consent=external_consent
    )

    return ApiResponse(success=True, data=status_dto, error=None)
