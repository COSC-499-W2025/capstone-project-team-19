from fastapi import APIRouter, Depends
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse
from src.api.schemas.portfolio import PortfolioDTO, PortfolioItemDTO
from src.services.portfolio_service import get_portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=ApiResponse[PortfolioDTO])
def get_portfolio_for_user(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    items = get_portfolio(conn, user_id)
    dto = PortfolioDTO(items=[PortfolioItemDTO(**item) for item in items])
    return ApiResponse(success=True, data=dto, error=None)