import os
import asyncio
import logging
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder


from app.core.database import (
    fetch_tracked_stocks, add_tracked_stock, untrack_stock,
    fetch_recent_prices, fetch_max_price_days
)
from app.core.actions import extract_stock_pipeline, extract_balance_sheet_pipeline

# 🛠️ Explicitly declare the path namespace right here!
router = APIRouter(prefix="/control-panel")
logger = logging.getLogger("uvicorn.error")

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.normpath(os.path.join(current_dir, "..", "..", "templates"))
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def get_control_panel_page(request: Request):
    return templates.TemplateResponse(request=request, name="control_panel.html")

@router.websocket("/ws")
async def control_panel_subscription_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("[WS] Client connected to live dashboard stream.")
    try:
        while True:
            try:
                stocks, max_days, history = await asyncio.gather(
                    fetch_tracked_stocks(),
                    fetch_max_price_days(),
                    fetch_recent_prices(per_stock_limit=10)
                )
                
                # 🛠️ Sanitize the data structures into JSON-safe primitives
                safe_payload = jsonable_encoder({
                    "stocks": stocks,
                    "max_days": max_days,
                    "history": history
                })
                
                logger.info(
                    f"[WS] Broadcasting: {len(stocks)} stocks | "
                    f"{len(max_days)} high records | {len(history)} price rows"
                )
                
                # Send the clean, encoded payload
                await websocket.send_json(safe_payload)
                
            except Exception as query_err:
                logger.error(f"[WS] Database extraction error: {str(query_err)}")
            
            await asyncio.sleep(1.5)
            
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected from live dashboard stream.")

# --- Action Gateway Endpoints ---

class StockCreatePayload(BaseModel):
    ticker: str
    company_name: str

@router.post("/api/v1/control/stocks")
async def api_add_stock(payload: StockCreatePayload):
    await add_tracked_stock(payload.ticker, payload.company_name)
    return {"status": "success"}

@router.post("/api/v1/control/stocks/untrack/{ticker}")
async def api_untrack_stock(ticker: str):
    await untrack_stock(ticker)
    return {"status": "success"}

@router.post("/api/v1/control/stocks/sync")
async def api_sync_pipelines():
    stocks = await fetch_tracked_stocks()
    for stock in stocks:
        await extract_stock_pipeline(stock["ticker"])
        await extract_balance_sheet_pipeline(stock["ticker"])
    return {"status": "completed"}