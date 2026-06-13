from typing import Optional
from app.core.db import get_pool, load_query
from app.core.logger import get_logger

logger = get_logger(__name__)

class GoldRepository:
    """Read-only data access layer serving the CLI and Web Dashboard."""

    @staticmethod
    async def fetch_recent_prices(limit: int = 10) -> list[dict]:
        pool = get_pool()
        query = load_query("fetch_recent_prices.sql")
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [dict(r) for r in rows]

    @staticmethod
    async def fetch_max_price_days(ticker: Optional[str] = None) -> list[dict]:
        pool = get_pool()
        query = load_query("get_max_price_days.sql")
        
        async with pool.acquire() as conn:
            # Matches your existing logic to pass None if no ticker provided
            rows = await conn.fetch(query, ticker.upper() if ticker else None)
            return [dict(r) for r in rows]
            
    @staticmethod
    async def refresh_materialized_views() -> None:
        """Triggers the refresh for the Gold layer."""
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_daily_prices")
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_balance_sheets")
            logger.info("Gold Materialized views refreshed successfully.")