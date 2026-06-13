import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.repositories.stock_repo import StockRepository
from app.repositories.bronze_repo import BronzeRepository
import json

@pytest.mark.asyncio
@patch("app.repositories.stock_repo.get_pool")
@patch("app.repositories.stock_repo.load_query")
async def test_stock_repo_untrack_stock(mock_load_query, mock_get_pool):
    mock_load_query.return_value = "UPDATE dim_stocks SET should_fetch = FALSE WHERE ticker = $1;"
    
    # Mocking asyncpg.Pool and its acquire() context manager
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool

    await StockRepository.untrack_stock("AAPL")

    mock_load_query.assert_called_once_with("untrack_stock.sql")
    mock_conn.execute.assert_called_once_with("UPDATE dim_stocks SET should_fetch = FALSE WHERE ticker = $1;", "AAPL")


@pytest.mark.asyncio
@patch("app.repositories.bronze_repo.get_pool")
@patch("app.repositories.bronze_repo.load_query")
async def test_bronze_repo_insert_response(mock_load_query, mock_get_pool):
    mock_load_query.return_value = "INSERT INTO bronze..."
    
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool

    test_payload = {"some": "data"}
    await BronzeRepository.insert_response("API_CALL", "AAPL", "SUCCESS", test_payload)

    mock_conn.execute.assert_called_once_with(
        "INSERT INTO bronze...", 
        "API_CALL", 
        "AAPL", 
        "SUCCESS", 
        json.dumps(test_payload)
    )