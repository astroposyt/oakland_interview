from typing import List
from app.core.db import get_pool, load_query
from app.core.logger import get_logger
from app.schemas.prices import DailyPriceRecord
from app.schemas.balance_sheets import BalanceSheetRecord

logger = get_logger(__name__)

class SilverRepository:
    """Handles operations for the Silver layer (Normalized Fact Tables)."""

    @staticmethod
    async def _get_stock_id(conn, ticker: str) -> int:
        query = load_query("get_or_create_stock.sql")
        return await conn.fetchval(query, ticker.upper(), f"{ticker.upper()} Inc")

    @staticmethod
    async def upsert_prices(ticker: str, records: List[DailyPriceRecord]) -> None:
        pool = get_pool()
        query = load_query("upsert_prices.sql")
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                stock_id = await SilverRepository._get_stock_id(conn, ticker)
                
                # Prepare data for bulk insert
                values = [
                    (stock_id, rec.price_date, rec.open_price, rec.high_price, 
                     rec.low_price, rec.close_price, rec.volume)
                    for rec in records
                ]
                
                # Execute in bulk (Massive performance boost over loops)
                await conn.executemany(query, values)
                
        logger.info(f"Loaded {len(records)} price records into Silver for {ticker}")

    @staticmethod
    async def upsert_balance_sheets(ticker: str, records: List[BalanceSheetRecord], period_type: str) -> None:
        pool = get_pool()
        query = load_query("upsert_balance_sheets.sql")
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                stock_id = await SilverRepository._get_stock_id(conn, ticker)
                
                values = [
                    (stock_id, rec.fiscal_date_ending, period_type, rec.reported_currency, 
                     rec.total_assets, rec.total_current_assets, rec.cash_and_cash_equivalents, 
                     rec.cash_and_short_term_investments, rec.inventory, rec.current_net_receivables,
                     rec.total_non_current_assets, rec.property_plant_equipment, rec.accumulated_depreciation, 
                     rec.intangible_assets, rec.goodwill, rec.short_term_investments, rec.total_liabilities, 
                     rec.total_current_liabilities, rec.current_accounts_payable, rec.short_term_debt, 
                     rec.total_non_current_liabilities, rec.long_term_debt, rec.total_shareholder_equity,
                     rec.retained_earnings, rec.common_stock, rec.shares_outstanding)
                    for rec in records
                ]
                
                await conn.executemany(query, values)
                
        logger.info(f"Loaded {len(records)} {period_type} balance sheets into Silver for {ticker}")

    @staticmethod
    async def fetch_diagnostic_silver_prices(limit: int = 20) -> List[dict]:
        """Dumps the direct rows of the clean, normalized pricing fact table."""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT s.ticker, p.price_date, p.open_price, p.high_price, p.low_price, p.close_price, p.volume 
                   FROM fact_daily_prices p 
                   JOIN dim_stocks s ON p.stock_id = s.id 
                   ORDER BY p.price_date DESC LIMIT $1;""",
                limit
            )
            return [dict(r) for r in rows]

    @staticmethod
    async def fetch_diagnostic_silver_balances(limit: int = 20) -> List[dict]:
        """Dumps the direct rows of the normalized accounting balance sheet fact table."""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT s.ticker, b.fiscal_date_ending, b.period_type, b.reported_currency, b.total_assets, b.total_liabilities, b.total_shareholder_equity 
                   FROM fact_balance_sheets b 
                   JOIN dim_stocks s ON b.stock_id = s.id 
                   ORDER BY b.fiscal_date_ending DESC LIMIT $1;""",
                limit
            )
            return [dict(r) for r in rows]