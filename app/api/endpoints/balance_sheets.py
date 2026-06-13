from fastapi import APIRouter, HTTPException
from app.core.actions import extract_balance_sheet_pipeline

router = APIRouter()

@router.get("/api/balance-sheet/{ticker}")
async def get_balance_sheet_data(ticker: str):
    try:
        payload = await extract_balance_sheet_pipeline(ticker)
        if "Error Message" in payload:
            raise HTTPException(status_code=404, detail=payload["Error Message"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))