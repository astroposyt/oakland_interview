from typing import Optional, List
from app.core.db import get_pool, load_query
from app.core.logger import get_logger

logger = get_logger(__name__)

class GoldRepository:
    """Read-only data access layer serving analytical outputs to the CLI and Web Dashboard."""

    @staticmethod
    async def fetch_recent_prices(limit: int = 10) -> List[dict]:
        """Fetches partitioned window-slices from the fact table for the dashboard log."""
        pool = get_pool()
        query = load_query("fetch_recent_prices.sql")
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [dict(r) for r in rows]

    @staticmethod
    async def fetch_max_price_days(ticker: Optional[str] = None) -> List[dict]:
        """Tracks down metrics defining all-time peak trading valuation points."""
        pool = get_pool()
        query = load_query("get_max_price_days.sql")
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, ticker.upper() if ticker else None)
            return [dict(r) for r in rows]

    @staticmethod
    async def fetch_latest_gold_prices() -> List[dict]:
        """Queries active aggregated reporting metrics out of the Gold daily pricing view."""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM gold_latest_daily_prices;")
            return [dict(r) for r in rows]

    @staticmethod
    async def fetch_latest_gold_balance_sheets(period_type: str) -> List[dict]:
        """Queries clean accounting histories directly from the Gold fundamental view."""
        pool = get_pool()
        query = load_query("fetch_latest_gold_balance_sheets.sql")
        async with pool.acquire() as conn:
            # Enforce capitalization to match standard DB entries ('Annual' / 'Quarterly')
            rows = await conn.fetch(query, period_type.capitalize())
            return [dict(r) for r in rows]

    @staticmethod
    async def refresh_materialized_views() -> None:
        """Triggers transactional updates to re-compile background materialized view states."""
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_daily_prices;")
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_balance_sheets;")
            logger.info("Materialized views refreshed successfully.")