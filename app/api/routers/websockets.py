import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Streaming"])

@router.websocket("/ws/dashboard")
async def live_dashboard_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to live dashboard stream.")
    try:
        while True:
            stocks, max_days, history = await asyncio.gather(
                StockRepository.fetch_tracked_stocks(),
                GoldRepository.fetch_max_price_days(),
                GoldRepository.fetch_recent_prices(limit=10)
            )
            
            safe_payload = jsonable_encoder({
                "stocks": stocks,
                "max_days": max_days,
                "history": history
            })
            
            await websocket.send_json(safe_payload)
            await asyncio.sleep(1.5)
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from live dashboard stream.")
    except Exception as e:
        logger.error(f"Websocket error: {e}")