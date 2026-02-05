from __future__ import annotations
from sqlite3 import Connection
from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.project_dates import (
    PatchProjectDatesRequestDTO,
    ProjectDatesItemDTO,
    ProjectDatesListDTO,
    ResetProjectDatesResultDTO,
)

from src.services.project_dates_service import (
    UNSET,
    clear_all_manual_project_dates,
    clear_project_manual_dates,
    list_project_dates,
    set_project_manual_dates,
    validate_manual_date_range,
)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/dates", response_model=ApiResponse[ProjectDatesListDTO])
def get_project_dates(user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    items = list_project_dates(conn, user_id)
    dto = ProjectDatesListDTO(projects=[ProjectDatesItemDTO(**i.__dict__) for i in items])
    return ApiResponse(success=True, data=dto, error=None)

@router.patch("/{project_id:int}/dates", response_model=ApiResponse[ProjectDatesItemDTO])
def patch_project_dates(project_id: int, body: PatchProjectDatesRequestDTO, request: Request, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    # Distinguish "field omitted" vs "explicit null"
    start_provided = "start_date" in body.model_fields_set
    end_provided = "end_date" in body.model_fields_set

    if not start_provided and not end_provided:
        raise HTTPException(status_code=422, detail="At least one of start_date or end_date is required.")

    start_value = body.start_date if start_provided else UNSET
    end_value = body.end_date if end_provided else UNSET

    # Validate only when we have concrete values (strings or None).
    start_for_validation = None if start_value is UNSET else start_value
    end_for_validation = None if end_value is UNSET else end_value
    try:
        validate_manual_date_range(start_for_validation, end_for_validation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=e.args[0])

    try:
        item = set_project_manual_dates(
            conn,
            user_id,
            project_id,
            start_date=start_value,
            end_date=end_value,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=e.args[0])

    return ApiResponse(success=True, data=ProjectDatesItemDTO(**item.__dict__), error=None)

@router.delete("/{project_id:int}/dates", response_model=ApiResponse[ProjectDatesItemDTO])
def delete_project_dates(project_id: int, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    try:
        item = clear_project_manual_dates(conn, user_id, project_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0])

    return ApiResponse(success=True, data=ProjectDatesItemDTO(**item.__dict__), error=None)

@router.post("/dates/reset", response_model=ApiResponse[ResetProjectDatesResultDTO])
def post_project_dates_reset(user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    cleared_count = clear_all_manual_project_dates(conn, user_id)
    return ApiResponse(success=True, data=ResetProjectDatesResultDTO(cleared_count=cleared_count), error=None)
