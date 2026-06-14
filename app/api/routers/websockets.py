import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.core.logger import get_logger
from app.repositories.bronze_repo import BronzeRepository
from app.repositories.silver_repo import SilverRepository

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


@router.websocket("/ws/pipeline")
async def live_pipeline_stream(websocket: WebSocket):
    """Streams the live state of the Medallion pipeline layers."""
    await websocket.accept()
    logger.info("Client connected to live pipeline stream.")
    try:
        while True:
            pending_syncs, bronze_rows, silver_prices, gold_prices = await asyncio.gather(
                StockRepository.fetch_stocks_needing_price_sync(),
                BronzeRepository.fetch_diagnostic_bronze(limit=3),
                SilverRepository.fetch_diagnostic_silver_prices(limit=6),
                GoldRepository.fetch_latest_gold_prices()
            )
            
            pricing_bronze = [r for r in bronze_rows if r['api_called'] == 'TIME_SERIES_DAILY']

            safe_payload = jsonable_encoder({
                "pending_syncs": pending_syncs,
                "bronze_data": pricing_bronze,
                "silver_data": silver_prices,
                "gold_data": gold_prices
            })
            
            await websocket.send_json(safe_payload)
            await asyncio.sleep(1.5)  # Update every 1.5 seconds
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from pipeline stream.")
    except Exception as e:
        logger.error(f"Pipeline Websocket error: {e}")