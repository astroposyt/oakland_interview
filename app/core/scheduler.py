import asyncio
import datetime
import logging

from app.core.database import fetch_tracked_stocks
from app.core.actions import extract_stock_pipeline, extract_balance_sheet_pipeline

logger = logging.getLogger("uvicorn.error")

async def cron_sync_scheduler():
    logger.info("[CRON] Simplified wall-clock scheduler active. Watching for 17:00 and 17:05 daily.")
    
    last_fired_minute = -1
    
    while True:
        now = datetime.datetime.now()
        
        if now.hour == 17 and now.minute in (0, 5):
            
            if now.minute != last_fired_minute:
                last_fired_minute = now.minute
                logger.info(f"[CRON] Target reached ({now.strftime('%H:%M')}). Executing data sync cascade...")
                
                try:
                    stocks = await fetch_tracked_stocks()
                    if not stocks:
                        logger.info("[CRON] Sync skipped: No active monitored stocks found.")
                        continue
                        
                    for stock in stocks:
                        ticker = stock["ticker"]
                        logger.info(f"[CRON][{ticker}] Processing Medallion pipelines...")
                        await extract_stock_pipeline(ticker)
                        await extract_balance_sheet_pipeline(ticker)
                        
                    logger.info("[CRON] Batch execution completed successfully.")
                except Exception as err:
                    logger.error(f"[CRON] Pipeline failed: {str(err)}")
        
        if now.minute not in (0, 5):
            last_fired_minute = -1
            
        await asyncio.sleep(30)