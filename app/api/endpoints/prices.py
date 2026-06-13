from fastapi import APIRouter, HTTPException
from app.core.actions import extract_stock_pipeline

router = APIRouter()

@router.get("/api/stocks/{ticker}")
async def get_stock_data(ticker: str):
    try:
        payload = await extract_stock_pipeline(ticker)
        if "Error Message" in payload:
            raise HTTPException(status_code=404, detail=payload["Error Message"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))