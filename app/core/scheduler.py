import os
import httpx
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.services.ingestion_service import StockIngestionService

logger = logging.getLogger("oakland.scheduler")

#This doesnt connect to a real url at the moment, just added the logic as I would have this in production
async def ping_deadmans_switch():
    """Pings an external heartbeat monitor (e.g., Healthchecks.io)"""
    url = os.getenv("DEADMANS_SWITCH_URL")
    if not url:
        return  
    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(url)
            logger.debug("Deadman's switch heartbeat sent.")
    except Exception as e:
        logger.warning(f"Failed to ping Deadman's switch: {str(e)}")

async def sync_all_stocks():
    logger.info("[CRON] Executing 5-minute data sync cascade...")
    try:
        stocks = await StockRepository.fetch_tracked_stocks()
        if not stocks:
            logger.info("[CRON] Sync skipped: No active monitored stocks found.")
            return
            
        for stock in stocks:
            ticker = stock["ticker"]
            logger.info(f"[CRON][{ticker}] Processing Medallion pipelines...")
            await StockIngestionService.process_daily_prices(ticker)
            await StockIngestionService.process_balance_sheets(ticker)
            
        logger.info("[CRON] Pipeline extractions complete. Refreshing Gold views...")
        await GoldRepository.refresh_materialized_views()
        
    except Exception as err:
        logger.exception(f"[CRON] Pipeline failed: {str(err)}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_all_stocks, 'interval', minutes=5)
    scheduler.start()
    logger.info("[CRON] APScheduler active. Syncing every 5 minutes.")