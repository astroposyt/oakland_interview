import pytest
from unittest.mock import patch, AsyncMock
from app.services.ingestion_service import StockIngestionService

@pytest.mark.asyncio
@patch("app.services.ingestion_service.BronzeRepository")
@patch("app.services.ingestion_service.SilverRepository")
@patch("app.services.ingestion_service.get_api_client")
async def test_process_daily_prices_success(mock_get_client, mock_silver, mock_bronze, sample_raw_price_data):

    mock_client_instance = AsyncMock()
    mock_client_instance.fetch_stock_data.return_value = sample_raw_price_data
    mock_get_client.return_value = mock_client_instance
    
    mock_bronze.insert_response = AsyncMock()
    mock_silver.upsert_prices = AsyncMock()

    result = await StockIngestionService.process_daily_prices("AAPL")

    mock_client_instance.fetch_stock_data.assert_called_once_with("AAPL")
    
    mock_bronze.insert_response.assert_called_once_with(
        "TIME_SERIES_DAILY", "AAPL", "SUCCESS", sample_raw_price_data
    )

    mock_silver.upsert_prices.assert_called_once()
    assert result == sample_raw_price_data


@pytest.mark.asyncio
@patch("app.services.ingestion_service.BronzeRepository")
@patch("app.services.ingestion_service.SilverRepository")
@patch("app.services.ingestion_service.get_api_client")
async def test_process_daily_prices_halts_on_api_error(mock_get_client, mock_silver, mock_bronze, sample_api_error):

    mock_client_instance = AsyncMock()
    mock_client_instance.fetch_stock_data.return_value = sample_api_error
    mock_get_client.return_value = mock_client_instance
    
    mock_bronze.insert_response = AsyncMock()
    mock_silver.upsert_prices = AsyncMock()

    result = await StockIngestionService.process_daily_prices("INVALID")

    mock_bronze.insert_response.assert_called_once_with(
        "TIME_SERIES_DAILY", "INVALID", "ERROR", sample_api_error
    )
    
    mock_silver.upsert_prices.assert_not_called()
    assert "Error Message" in result


@pytest.mark.asyncio
@patch("app.services.ingestion_service.BronzeRepository")
@patch("app.services.ingestion_service.get_api_client")
async def test_process_daily_prices_raises_validation_error(mock_get_client, mock_bronze):
    corrupt_data = {"Time Series (Daily)": {"2026-06-12": {"1. open": "NOT_A_NUMBER"}}}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.fetch_stock_data.return_value = corrupt_data
    mock_get_client.return_value = mock_client_instance
    mock_bronze.insert_response = AsyncMock()

    with pytest.raises(ValueError, match="Data schema changed or invalid"):
        await StockIngestionService.process_daily_prices("AAPL")