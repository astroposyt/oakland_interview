import os
import json
import logging
import asyncpg
from app.schemas.prices import DailyPriceRecord
from app.schemas.balance_sheets import BalanceSheetRecord
from typing import Optional

logger = logging.getLogger("uvicorn.error")

async def get_db_connection():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

def load_query(filename: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "queries", filename)
    with open(file_path, "r") as file:
        return file.read()

async def insert_bronze_response(api_called: str, ticker: str, status: str, response_json: dict) -> None:
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO bronze_api_responses (api_called, ticker, status, response_json)
            VALUES ($1, $2, $3, $4)
            """,
            api_called, ticker.upper(), status, json.dumps(response_json)
        )
    finally:
        await conn.close()

async def get_or_create_stock_id(conn, ticker: str) -> int:
    query = load_query("get_or_create_stock.sql")
    return await conn.fetchval(query, ticker.upper(), f"{ticker.upper()} Inc")

async def upsert_silver_prices(ticker: str, records: list[DailyPriceRecord]) -> None:
    conn = await get_db_connection()
    query = load_query("upsert_prices.sql")
    try:
        async with conn.transaction():
            stock_id = await get_or_create_stock_id(conn, ticker)
            for rec in records:
                await conn.execute(
                    query,
                    stock_id, rec.price_date, rec.open_price, rec.high_price, rec.low_price, rec.close_price, rec.volume
                )
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_daily_prices")
            logger.info(f"Successfully loaded {len(records)} price records into Silver for {ticker}")
    finally:
        await conn.close()

async def upsert_silver_balance_sheets(ticker: str, records: list[BalanceSheetRecord], period_type: str) -> None:
    conn = await get_db_connection()
    query = load_query("upsert_balance_sheets.sql")
    try:
        async with conn.transaction():
            stock_id = await get_or_create_stock_id(conn, ticker)
            for rec in records:
                await conn.execute(
                    query,
                    stock_id, rec.fiscal_date_ending, period_type, rec.reported_currency, rec.total_assets, rec.total_current_assets,
                    rec.cash_and_cash_equivalents, rec.cash_and_short_term_investments, rec.inventory, rec.current_net_receivables,
                    rec.total_non_current_assets, rec.property_plant_equipment, rec.accumulated_depreciation, rec.intangible_assets,
                    rec.goodwill, rec.short_term_investments, rec.total_liabilities, rec.total_current_liabilities, rec.current_accounts_payable,
                    rec.short_term_debt, rec.total_non_current_liabilities, rec.long_term_debt, rec.total_shareholder_equity,
                    rec.retained_earnings, rec.common_stock, rec.shares_outstanding
                )
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gold_latest_balance_sheets")
            logger.info(f"Successfully loaded {len(records)} {period_type} balance sheets into Silver for {ticker}")
    finally:
        await conn.close()

async def fetch_latest_gold_prices() -> list[dict]:
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM gold_latest_daily_prices")
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def fetch_latest_gold_balance_sheets(period_type: str) -> list[dict]:
    conn = await get_db_connection()
    try:
        query = load_query("fetch_latest_gold_balance_sheets.sql")
        rows = await conn.fetch(query, period_type.capitalize())
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def add_tracked_stock(ticker: str, company_name: str) -> None:
    conn = await get_db_connection()
    try:
        query = load_query("add_tracked_stock.sql")
        await conn.execute(query, ticker.upper(), company_name)
    finally:
        await conn.close()

async def fetch_tracked_stocks() -> list[dict]:
    conn = await get_db_connection()
    try:
        query = load_query("list_tracked_stocks.sql")
        rows = await conn.fetch(query)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def untrack_stock(ticker: str) -> None:
    conn = await get_db_connection()
    try:
        query = load_query("untrack_stock.sql")
        await conn.execute(query, ticker.upper())
    finally:
        await conn.close()

async def fetch_recent_prices(per_stock_limit: int = 10) -> list[dict]:
    conn = await get_db_connection()
    try:
        query = load_query("fetch_recent_prices.sql")
        rows = await conn.fetch(query, per_stock_limit)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def fetch_recent_balance_sheets(period_type: str, per_stock_limit: int = 10) -> list[dict]:
    conn = await get_db_connection()
    try:
        query = load_query("fetch_recent_balance_sheets.sql")
        rows = await conn.fetch(query, period_type.capitalize(), per_stock_limit)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def fetch_max_price_days(ticker: Optional[str] = None) -> list[dict]:
    conn = await get_db_connection()
    try:
        query = load_query("get_max_price_days.sql")
        param = ticker.upper() if ticker else None
        rows = await conn.fetch(query, param)
        return [dict(r) for r in rows]
    finally:
        await conn.close()