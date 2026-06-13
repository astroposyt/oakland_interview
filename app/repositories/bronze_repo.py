import json
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