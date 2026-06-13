import pytest
from app.core.actions import ingest_stock_data

@pytest.mark.asyncio
async def test_tracer_bullet_action():
    result = await ingest_stock_data("AAPL")
    assert result["status"] == "success"
    assert result["ticker"] == "AAPL"