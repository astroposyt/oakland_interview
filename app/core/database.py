import os
import json
import logging
import asyncpg
from typing import Optional, Any
from app.schemas.prices import DailyPriceRecord
from app.schemas.balance_sheets import BalanceSheetRecord
from app.core import queries 

logger = logging.getLogger("uvicorn.error")

db_pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> None:
    """Initializes a shared reusable pool of 1 to 10 active database connections."""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"), 
            min_size=1, 
            max_size=10
        )
        logger.info("Database connection pool initialized.")

async def close_db_pool() -> None:
    """Cleanly closes down all active connection paths inside the cluster pool."""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
        logger.info("Database connection pool closed.")


def load_query(query_name: str) -> str:
    """Helper utility to load raw SQL script code strings from external disk locations."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    query_path = os.path.join(current_dir, "queries", query_name)
    with open(query_path, "r") as f:
        return f.read()



async def insert_bronze_response(api_called: str, ticker: str, status: str, response_json: dict) -> None:
    """Dumps raw, unprocessed JSON API data strings directly into the Bronze audit logs."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO bronze_api_responses (api_called, ticker, status, response_json)
            VALUES ($1, $2, $3, $4)
            """,
            api_called, ticker.upper(), status, json.dumps(response_json)
        )

async def get_or_create_stock_id(conn: asyncpg.Connection, ticker: str) -> int:
    """Internal transaction utility helper to locate or map primary identity key definitions."""
    return await conn.fetchval(queries.GET_OR_CREATE_STOCK, ticker.upper(), f"{ticker.upper()} Inc")

async def upsert_silver_prices(ticker: str, records: list[DailyPriceRecord]) -> None:
    """Transforms and saves cleaned, structured pricing metrics into Silver fact tables."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            stock_id = await get_or_create_stock_id(conn, ticker)
            for rec in records:
                await conn.execute(
                    queries.UPSERT_PRICES,
                    stock_id, rec.price_date, rec.open_price, rec.high_price, 
                    rec.low_price, rec.close_price, rec.volume
                )
            logger.info(f"Successfully loaded {len(records)} price records into Silver for {ticker}")

async def upsert_silver_balance_sheets(ticker: str, records: list[BalanceSheetRecord], period_type: str) -> None:
    """Transforms and saves clean fundamental records into Silver fundamental ledgers."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            stock_id = await get_or_create_stock_id(conn, ticker)
            for rec in records:
                await conn.execute(
                    queries.UPSERT_BALANCE_SHEETS,
                    stock_id, rec.fiscal_date_ending, period_type, rec.reported_currency, 
                    rec.total_assets, rec.total_current_assets, rec.cash_and_cash_equivalents, 
                    rec.cash_and_short_term_investments, rec.inventory, rec.current_net_receivables,
                    rec.total_non_current_assets, rec.property_plant_equipment, rec.accumulated_depreciation, 
                    rec.intangible_assets, rec.goodwill, rec.short_term_investments, rec.total_liabilities, 
                    rec.total_current_liabilities, rec.current_accounts_payable, rec.short_term_debt, 
                    rec.total_non_current_liabilities, rec.long_term_debt, rec.total_shareholder_equity,
                    rec.retained_earnings, rec.common_stock, rec.shares_outstanding
                )
            logger.info(f"Successfully loaded {len(records)} {period_type} balance sheets into Silver for {ticker}")


async def refresh_materialized_views() -> None:
    """Triggers hot execution refreshes to re-compile your background materialized view states."""
    async with db_pool.acquire() as conn:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_daily_prices")
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_balance_sheets")
        logger.info("Materialized views refreshed successfully.")

async def add_tracked_stock(ticker: str, company_name: str) -> None:
    """Registers a fresh asset target to actively monitor, handling upsert collisions safely."""
    async with db_pool.acquire() as conn:
        query = load_query("add_tracked_stock.sql")
        await conn.execute(query, ticker.upper(), company_name)

async def untrack_stock(ticker: str) -> None:
    """Toggles asset monitoring trace configurations off without clearing historical data pools."""
    async with db_pool.acquire() as conn:
        query = load_query("untrack_stock.sql")
        await conn.execute(query, ticker.upper())

async def fetch_tracked_stocks() -> list[dict]:
    """Retrieves all corporate listings currently registered for active daily updates."""
    async with db_pool.acquire() as conn:
        query = load_query("list_tracked_stocks.sql")
        rows = await conn.fetch(query)
        return [dict(r) for r in rows]

async def fetch_latest_gold_prices() -> list[dict]:
    """Queries active aggregated reporting metrics directly out of the Gold daily pricing view."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM gold_latest_daily_prices")
        return [dict(r) for r in rows]

async def fetch_latest_gold_balance_sheets(period_type: str) -> list[dict]:
    """Queries clean accounting histories directly from Gold fundamental tables."""
    async with db_pool.acquire() as conn:
        query = load_query("fetch_latest_gold_balance_sheets.sql")
        rows = await conn.fetch(query, period_type.capitalize())
        return [dict(r) for r in rows]

async def fetch_recent_prices(per_stock_limit: int = 10) -> list[dict]:
    """Extracts partitioned window-slices representing current chronological values."""
    async with db_pool.acquire() as conn:
        query = load_query("fetch_recent_prices.sql")
        rows = await conn.fetch(query, per_stock_limit)
        return [dict(r) for r in rows]

async def fetch_recent_balance_sheets(period_type: str, per_stock_limit: int = 10) -> list[dict]:
    """Extracts chronological blocks covering partitioned financial sheets out of Silver."""
    async with db_pool.acquire() as conn:
        query = load_query("fetch_recent_balance_sheets.sql")
        rows = await conn.fetch(query, period_type.capitalize(), per_stock_limit)
        return [dict(r) for r in rows]

async def fetch_max_price_days(ticker: Optional[str] = None) -> list[dict]:
    """Tracks down transaction metrics defining all-time peak trading valuation points."""
    async with db_pool.acquire() as conn:
        query = load_query("get_max_price_days.sql")
        param = ticker.upper() if ticker else None
        rows = await conn.fetch(query, param)
        return [dict(r) for r in rows]