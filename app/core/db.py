import os
import asyncpg
from typing import Optional
from functools import lru_cache
from app.core.logger import get_logger

logger = get_logger(__name__)

_pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"), 
            min_size=1, max_size=10
        )
        logger.info("Database connection pool initialized.")

async def close_db_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool

@lru_cache(maxsize=None)
def load_query(query_name: str) -> str:
    """
    Loads SQL from disk and caches it in memory.
    Prevents file I/O bottlenecks during high-speed execution.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    query_path = os.path.join(current_dir, "queries", query_name)
    with open(query_path, "r") as f:
        return f.read()