import pytest
import app.core.actions
from app.schemas.prices import AlphaVantagePriceParser
from app.core.actions import _orchestrate_pipeline, extract_stock_pipeline

@pytest.mark.asyncio
async def test_pipeline_orchestrator_exits_early_on_api_error_message():
    async def mock_fetch_error(ticker: str):
        return {"Error Message": "Invalid API Key or Ticker Symbol Provided"}

    async def dummy_silver_handler(parsed):
        pass

    mock_insert_called = False
    async def mock_insert_bronze(api, ticker, status, json_data):
        nonlocal mock_insert_called
        mock_insert_called = True

    app.core.actions.insert_bronze_response = mock_insert_bronze

    result = await _orchestrate_pipeline(
        ticker="INVALID",
        api_called="TIME_SERIES_DAILY",
        fetch_handler=mock_fetch_error,
        parser_model=AlphaVantagePriceParser,
        silver_handler=dummy_silver_handler
    )

    assert mock_insert_called is True
    assert "Error Message" in result
    assert result["Error Message"] == "Invalid API Key or Ticker Symbol Provided"

@pytest.mark.asyncio
async def test_pipeline_orchestrator_raises_value_error_on_validation_failure():
    async def mock_fetch_corrupt(ticker: str):
        return {
            "Time Series (Daily)": {
                "2026-06-12": {"1. open": "CORRUPT"}
            }
        }

    async def dummy_silver_handler(parsed):
        pass

    async def mock_insert_bronze(api, ticker, status, json_data):
        pass

    app.core.actions.insert_bronze_response = mock_insert_bronze

    with pytest.raises(ValueError) as exc_info:
        await _orchestrate_pipeline(
            ticker="AAPL",
            api_called="TIME_SERIES_DAILY",
            fetch_handler=mock_fetch_corrupt,
            parser_model=AlphaVantagePriceParser,
            silver_handler=dummy_silver_handler
        )
    
    assert "Data validation failure encountered" in str(exc_info.value)

@pytest.mark.asyncio
async def test_extract_stock_pipeline_success_flow():
    async def mock_fetch_success(ticker: str):
        return {
            "Meta Data": {"2. Symbol": ticker},
            "Time Series (Daily)": {
                "2026-06-12": {
                    "1. open": "100.00", "2. high": "105.00", 
                    "3. low": "95.00", "4. close": "102.00", "5. volume": "1000"
                }
            }
        }

    bronze_called = False
    async def mock_insert_bronze(api, ticker, status, json_data):
        nonlocal bronze_called
        bronze_called = True

    silver_called = False
    async def mock_upsert_silver(ticker, records):
        nonlocal silver_called
        silver_called = True

    app.core.actions.insert_bronze_response = mock_insert_bronze
    app.core.actions.upsert_silver_prices = mock_upsert_silver

    result = await extract_stock_pipeline("AAPL")
    
    assert result is not None
    assert bronze_called is True
    assert silver_called is True