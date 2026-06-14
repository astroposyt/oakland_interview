import os
import httpx
import logging
import asyncio
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
    logger.info("[CRON] Executing daily data sync cascade...")
    try:
        stocks = await StockRepository.fetch_tracked_stocks()
        if not stocks:
            logger.info("[CRON] Sync skipped: No active monitored stocks found.")
            await ping_deadmans_switch()
            return
            
        synced_any = False
        for stock in stocks:
            ticker = stock["ticker"]

            try:
                logger.info(f"[CRON][{ticker}] Processing Medallion pipelines...")
                await StockIngestionService.process_daily_prices(ticker)
                await StockIngestionService.process_balance_sheets(ticker)
                synced_any = True
                await asyncio.sleep(15)
            except Exception as asset_err:
                logger.error(f"[CRON][{ticker}] Pipeline failed for this asset: {str(asset_err)}")
                continue

        if synced_any:
            logger.info("[CRON] Refreshing Gold materialized views...")
            await GoldRepository.refresh_materialized_views()
            await ping_deadmans_switch()
        else:
            logger.warning("[CRON] All asset synchronizations failed during this run.")
            
    except Exception as err:
        logger.exception(f"[CRON] Critical top-level scheduler failure: {str(err)}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_all_stocks, 'cron', hour=0, minute=0)
    scheduler.start()
    logger.info("[CRON] APScheduler active. Syncing every 5 minutes.")