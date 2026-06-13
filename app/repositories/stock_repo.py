from app.core.db import get_pool, load_query
from app.core.logger import get_logger

logger = get_logger(__name__)

class StockRepository:
    """Manages the lifecycle of tracked assets in dim_stocks."""

    @staticmethod
    async def add_tracked_stock(ticker: str, company_name: str) -> None:
        pool = get_pool()
        query = load_query("add_tracked_stock.sql")
        
        async with pool.acquire() as conn:
            await conn.execute(query, ticker.upper(), company_name)
            logger.info(f"Registered {ticker.upper()} for monitoring.")

    @staticmethod
    async def untrack_stock(ticker: str) -> None:
        pool = get_pool()
        query = load_query("untrack_stock.sql")
        
        async with pool.acquire() as conn:
            await conn.execute(query, ticker.upper())
            logger.info(f"Untracked {ticker.upper()}.")

    @staticmethod
    async def fetch_tracked_stocks() -> list[dict]:
        pool = get_pool()
        query = load_query("list_tracked_stocks.sql")
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(r) for r in rows]