from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.portfolio import PortfolioDetailDTO, PortfolioGenerateRequestDTO
from src.services.portfolio_service import generate_portfolio

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
