import pytest
from app.core.actions import extract_stock_pipeline

@pytest.mark.asyncio
async def test_extract_stock_pipeline():
    ticker = "AAPL"
    result = await extract_stock_pipeline(ticker)
    assert result is not None
    assert "Meta Data" in result