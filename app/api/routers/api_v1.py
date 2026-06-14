from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from app.services.ingestion_service import StockIngestionService
from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.core.logger import get_logger

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1")

class StockCreatePayload(BaseModel):
    ticker: str
    company_name: str

@router.post("/control/stocks", tags=["Admin Control"])
async def add_stock(payload: StockCreatePayload):
    """Registers a new stock to be picked up by the next automated sync cycle."""
    try:
        await StockRepository.add_tracked_stock(payload.ticker, payload.company_name)
        
        return {
            "status": "success", 
            "message": f"Successfully registered {payload.ticker.upper()} for future tracking cycles."
        }
    except Exception as e:
        logger.error(f"Failed to add stock {payload.ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during stock registration.")

@router.post("/control/stocks/untrack/{ticker}", tags=["Admin Control"])
async def untrack_stock(ticker: str):
    """Stops the daily sync for a specific stock."""
    await StockRepository.untrack_stock(ticker)
    return {"status": "success", "message": f"{ticker} is no longer being tracked."}

@router.post("/control/stocks/sync", tags=["Admin Control"])
async def sync_all_tracked_stocks():
    """Manually triggers the ETL pipeline for all tracked stocks."""
    stocks = await StockRepository.fetch_tracked_stocks()
    for stock in stocks:
        await StockIngestionService.process_daily_prices(stock["ticker"])
        await StockIngestionService.process_balance_sheets(stock["ticker"])
    
    await GoldRepository.refresh_materialized_views()
    return {"status": "completed", "message": f"Successfully synced {len(stocks)} stocks."}


@router.get("/prices/{ticker}", tags=["Data Extraction"])
async def extract_stock_data(ticker: str):
    """Fetches the latest data from the API and pushes it through the pipeline."""
    try:
        payload = await StockIngestionService.process_daily_prices(ticker)
        if "Error Message" in payload:
            raise HTTPException(status_code=429, detail=payload["Error Message"])
        return payload
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/balance-sheets/extract/{ticker}", tags=["Data Extraction"])
async def extract_balance_sheets(ticker: str):
    """Fetches the latest balance sheets from the API and pushes them through the pipeline."""
    try:
        payload = await StockIngestionService.process_balance_sheets(ticker)
        if "Error Message" in payload:
            raise HTTPException(status_code=429, detail=payload["Error Message"])
        return payload
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/prices/latest/gold", tags=["Analytical Serving"])
async def get_latest_gold_prices():
    """Queries the processed Gold Materialized View directly for frontend display."""
    # Assumes you add this simple fetcher to the GoldRepository
    return await GoldRepository.fetch_latest_gold_prices()

@router.get("/balance-sheets/latest/gold", tags=["Analytical Serving"])
async def get_latest_gold_balance_sheets(
    period_type: str = Query("Annual", pattern="^(Annual|Quarterly)$")
):
    """Queries the clean accounting histories directly from the Gold layer."""
    # Assumes you add this simple fetcher to the GoldRepository
    return await GoldRepository.fetch_latest_gold_balance_sheets(period_type)