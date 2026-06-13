from fastapi import APIRouter, HTTPException
from app.core.actions import extract_stock_pipeline
from app.core.database import fetch_latest_gold_prices

router = APIRouter()

@router.get("/{ticker}")
async def get_stock_data(ticker: str):
    try:
        payload = await extract_stock_pipeline(ticker)
        if "Error Message" in payload:
            raise HTTPException(status_code=404, detail=payload["Error Message"])
        return payload
    except ValueError as e:
        # Catches our new Pydantic validation failures gracefully
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest/gold")
async def get_latest_prices():
    """Queries the processed Gold Materialized View directly"""
    return await fetch_latest_gold_prices()