from fastapi import APIRouter, HTTPException, Query
from app.core.actions import extract_balance_sheet_pipeline
from app.core.database import fetch_latest_gold_balance_sheets

router = APIRouter()

@router.post("/extract/{ticker}")
async def extract_balance_sheets(ticker: str):
    try:
        return await extract_balance_sheet_pipeline(ticker)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/latest")
async def get_latest_balance_sheets(
    period_type: str = Query("Annual", pattern="^(Annual|Quarterly)$")
):
    return await fetch_latest_gold_balance_sheets(period_type)