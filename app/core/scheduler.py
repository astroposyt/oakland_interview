import os
import httpx
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.services.ingestion_service import StockIngestionService
from app.core.logger import get_logger

logger = get_logger(__name__)

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

async def sync_daily_prices():
    """Fetches daily pricing data for stocks that haven't been synced today."""
    logger.info("[CRON] Executing daily price sync cascade...")
    try:
        stocks = await StockRepository.fetch_stocks_needing_price_sync()
        if not stocks:
            logger.info("[CRON] Sync skipped: All tracked stocks are already up-to-date for today.")
            await ping_deadmans_switch()
            return
            
        synced_any = False
        for stock in stocks:
            ticker = stock["ticker"]
            try:
                logger.info(f"[CRON][{ticker}] Processing Medallion pricing pipeline...")
                await StockIngestionService.process_daily_prices(ticker)
                
                await StockRepository.update_price_sync_time(ticker)
                synced_any = True
                
                await asyncio.sleep(15) 
            except Exception as asset_err:
                logger.error(f"[CRON][{ticker}] Price pipeline failed: {str(asset_err)}")
                continue

        if synced_any:
            logger.info("[CRON] Refreshing Gold materialized views...")
            await GoldRepository.refresh_materialized_views()
            await ping_deadmans_switch()
            
    except Exception as err:
        logger.exception(f"[CRON] Critical top-level scheduler failure (Prices): {str(err)}")


async def sync_balance_sheets():
    """Fetches financial statements for stocks that haven't been synced today."""
    logger.info("[CRON] Executing balance sheet sync cascade...")
    try:
        stocks = await StockRepository.fetch_stocks_needing_balance_sheet_sync()
        if not stocks:
            logger.info("[CRON] Sync skipped: All balance sheets are already up-to-date.")
            return
            
        for stock in stocks:
            ticker = stock["ticker"]
            try:
                logger.info(f"[CRON][{ticker}] Processing Medallion balance sheet pipeline...")
                await StockIngestionService.process_balance_sheets(ticker)
                
                await StockRepository.update_balance_sheet_sync_time(ticker)
                
                await asyncio.sleep(15) # Protect API Limits
            except Exception as asset_err:
                logger.error(f"[CRON][{ticker}] Balance sheet pipeline failed: {str(asset_err)}")
                continue
                
    except Exception as err:
        logger.exception(f"[CRON] Critical top-level scheduler failure (Balance Sheets): {str(err)}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_daily_prices, 'cron', hour=1, minute=0)
    scheduler.add_job(sync_balance_sheets, 'cron', day_of_week='sun', hour=2, minute=0)
    scheduler.start()
    logger.info("[CRON] APScheduler active. Pricing runs daily, Balance Sheets run weekly.")