import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.repositories.stock_repo import StockRepository
from app.repositories.bronze_repo import BronzeRepository
from app.repositories.gold_repo import GoldRepository
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

@pytest.mark.asyncio
@patch("app.repositories.gold_repo.get_pool")
async def test_gold_repo_fetch_latest_gold_prices(mock_get_pool):

    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool
    
    mock_conn.fetch.return_value = [{"ticker": "AAPL", "close_price": 150.0}]

    result = await GoldRepository.fetch_latest_gold_prices()

    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"
    mock_conn.fetch.assert_called_once_with("SELECT * FROM gold_latest_daily_prices;")


@pytest.mark.asyncio
@patch("app.repositories.gold_repo.get_pool")
@patch("app.repositories.gold_repo.load_query")
async def test_gold_repo_fetch_latest_gold_balance_sheets(mock_load_query, mock_get_pool):
    mock_load_query.return_value = "SELECT * FROM gold_latest_balance_sheets WHERE period_type = $1;"
    
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool
    
    await GoldRepository.fetch_latest_gold_balance_sheets("annual")

    mock_load_query.assert_called_once_with("fetch_latest_gold_balance_sheets.sql")
    mock_conn.fetch.assert_called_once_with(
        "SELECT * FROM gold_latest_balance_sheets WHERE period_type = $1;", 
        "Annual"
    )

@pytest.mark.asyncio
@patch("app.repositories.stock_repo.get_pool")
@patch("app.repositories.stock_repo.load_query")
async def test_stock_repo_fetch_stocks_needing_price_sync(mock_load_query, mock_get_pool):
    mock_load_query.return_value = "SELECT ticker FROM dim_stocks..."
    
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool
    mock_conn.fetch.return_value = [{"ticker": "AAPL", "company_name": "Apple Inc"}]

    result = await StockRepository.fetch_stocks_needing_price_sync()

    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"
    mock_load_query.assert_called_once_with("fetch_stocks_needing_price_sync.sql")


@pytest.mark.asyncio
@patch("app.repositories.stock_repo.get_pool")
@patch("app.repositories.stock_repo.load_query")
async def test_stock_repo_update_price_sync_time(mock_load_query, mock_get_pool):
    mock_load_query.return_value = "UPDATE dim_stocks SET last_price_sync_at..."
    
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_get_pool.return_value = mock_pool

    await StockRepository.update_price_sync_time("AAPL")

    mock_load_query.assert_called_once_with("update_price_sync_time.sql")
    mock_conn.execute.assert_called_once_with("UPDATE dim_stocks SET last_price_sync_at...", "AAPL")