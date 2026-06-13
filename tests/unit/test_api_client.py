import os
import pytest
from app.core.api_client import get_api_client, MockAlphaVantageClient, RealAlphaVantageClient

def test_factory_returns_mock_client_when_true(monkeypatch):
    monkeypatch.setenv("USE_MOCK_API", "true")
    client = get_api_client()
    assert isinstance(client, MockAlphaVantageClient)

def test_factory_returns_real_client_when_false(monkeypatch):
    monkeypatch.setenv("USE_MOCK_API", "false")
    client = get_api_client()
    assert isinstance(client, RealAlphaVantageClient)

@pytest.mark.asyncio
async def test_mock_client_resolves_lowercase_ticker():
    client = MockAlphaVantageClient()
    result = await client.fetch_stock_data("aapl")
    assert "Meta Data" in result
    assert result["Meta Data"]["2. Symbol"] == "AAPL"

@pytest.mark.asyncio
async def test_mock_client_fallback_handling():
    client = MockAlphaVantageClient()
    result = await client.fetch_stock_data("UNKNOWN")
    assert "Meta Data" in result
    assert result["Meta Data"]["2. Symbol"] == "UNKNOWN"

@pytest.mark.asyncio
async def test_mock_client_balance_sheet_fallback():
    client = MockAlphaVantageClient()
    result = await client.fetch_balance_sheet_data("XYZ")
    assert "symbol" in result
    assert result["symbol"] == "XYZ"