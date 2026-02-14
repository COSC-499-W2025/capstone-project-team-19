from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.helpers import resolve_project_name_for_edit
from src.api.schemas.common import ApiResponse
from src.api.schemas.portfolio import PortfolioDetailDTO, PortfolioGenerateRequestDTO, PortfolioEditRequestDTO
from src.services.portfolio_service import generate_portfolio, edit_portfolio, CorruptProjectDataError

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/generate", response_model=ApiResponse[PortfolioDetailDTO])
def post_portfolio_generate(
    request: PortfolioGenerateRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    result = generate_portfolio(conn, user_id, name=request.name)

    if not result:
        raise HTTPException(status_code=400, detail="No projects found for this user")

    dto = PortfolioDetailDTO(**result)
    return ApiResponse(success=True, data=dto, error=None)


@router.post("/edit", response_model=ApiResponse[PortfolioDetailDTO])
def post_portfolio_edit(
    request: PortfolioEditRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    project_name = resolve_project_name_for_edit(conn, user_id, request.project_summary_id)
    if not project_name:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = edit_portfolio(
            conn,
            user_id,
            project_name=project_name,
            scope=request.scope,
            display_name=request.display_name,
            summary_text=request.summary_text,
            contribution_bullets=request.contribution_bullets,
            name=request.name,
        )
    except CorruptProjectDataError:
        raise HTTPException(status_code=500, detail="Project data is corrupted")

    if not result:
        raise HTTPException(status_code=404, detail="Project not found")

    dto = PortfolioDetailDTO(**result)
    return ApiResponse(success=True, data=dto, error=None)
