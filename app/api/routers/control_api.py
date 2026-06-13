from fastapi import APIRouter
from app.repositories.stock_repo import StockRepository
from app.services.ingestion_service import StockIngestionService

router = APIRouter(prefix="/api/v1/control", tags=["Admin Actions"])

@router.post("/stocks")
async def add_stock(ticker: str, company_name: str):
    await StockRepository.add_tracked_stock(ticker, company_name)
    await StockIngestionService.process_daily_prices(ticker)
    return {"status": "success"}