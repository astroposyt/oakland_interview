import pytest
import app.core.actions
from app.core.actions import extract_stock_pipeline

@pytest.mark.asyncio
async def test_extract_stock_pipeline():
    async def mock_insert_bronze(*args, **kwargs):
        pass
        
    async def mock_upsert_silver(*args, **kwargs):
        pass

    app.core.actions.insert_bronze_response = mock_insert_bronze
    app.core.actions.upsert_silver_prices = mock_upsert_silver

    ticker = "AAPL"
    result = await extract_stock_pipeline(ticker)
    
    assert result is not None
    assert "Meta Data" in result