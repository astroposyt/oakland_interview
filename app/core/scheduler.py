import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import fetch_tracked_stocks, refresh_materialized_views
from app.core.actions import extract_stock_pipeline, extract_balance_sheet_pipeline

logger = logging.getLogger("uvicorn.error")

async def sync_all_stocks():
    logger.info("[CRON] Executing 5-minute data sync cascade...")
    try:
        stocks = await fetch_tracked_stocks()
        if not stocks:
            logger.info("[CRON] Sync skipped: No active monitored stocks found.")
            return
            
        for stock in stocks:
            ticker = stock["ticker"]
            logger.info(f"[CRON][{ticker}] Processing Medallion pipelines...")
            await extract_stock_pipeline(ticker)
            await extract_balance_sheet_pipeline(ticker)
            
        logger.info("[CRON] Pipeline extractions complete. Refreshing Gold views...")
        await refresh_materialized_views()
        
        logger.info("[CRON] Batch execution completed successfully.")
    except Exception as err:
        logger.exception(f"[CRON] Pipeline failed: {str(err)}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(sync_all_stocks, 'interval', minutes=5)
    
    scheduler.start()
    logger.info("[CRON] APScheduler active. Syncing every 5 minutes.")