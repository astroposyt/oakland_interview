import json
from typing import List
from app.core.db import get_pool, load_query
from app.core.logger import get_logger

logger = get_logger(__name__)

class BronzeRepository:
    """Immutable audit log for raw API payloads."""

    @staticmethod
    async def insert_response(api_called: str, ticker: str, status: str, response_json: dict) -> None:
        pool = get_pool()
        # Requires creating a new file: queries/insert_bronze_response.sql
        query = load_query("insert_bronze_response.sql") 
        
        async with pool.acquire() as conn:
            await conn.execute(
                query, 
                api_called, 
                ticker.upper(), 
                status, 
                json.dumps(response_json)
            )

    @staticmethod
    async def fetch_diagnostic_bronze(limit: int = 20) -> List[dict]:
        """Dumps the most recent immutable raw API payloads from Bronze."""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, api_called, ticker, status, extracted_at, response_json::text FROM bronze_api_responses ORDER BY extracted_at DESC LIMIT $1;",
                limit
            )
            return [dict(r) for r in rows]