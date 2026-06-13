import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from app.api.main import app

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client() -> TestClient:
    """Provides a synchronous TestClient for FastAPI router testing."""
    return TestClient(app)

@pytest.fixture
def sample_raw_price_data() -> dict:
    return {
        "Meta Data": {"2. Symbol": "AAPL"},
        "Time Series (Daily)": {
            "2026-06-12": {
                "1. open": "296.0300", "2. high": "297.1400",
                "3. low": "289.6200", "4. close": "291.1300", "5. volume": "38784789"
            }
        }
    }

@pytest.fixture
def sample_raw_balance_sheet() -> dict:
    return {
        "symbol": "AAPL",
        "annualReports": [
            {
                "fiscalDateEnding": "2025-09-30",
                "reportedCurrency": "USD",
                "totalAssets": "359241000000",
                "totalCurrentAssets": "147957000000",
                "cashAndCashEquivalentsAtCarryingValue": "35934000000",
                "cashAndShortTermInvestments": "35934000000",
                "inventory": "5718000000",
                "currentNetReceivables": "72957000000",
                "totalNonCurrentAssets": "211284000000",
                "propertyPlantEquipment": "61039000000",
                "accumulatedDepreciationAmortizationPPE": "None",
                "intangibleAssets": "None",
                "goodwill": "None",
                "shortTermInvestments": "18763000000",
                "totalLiabilities": "285508000000",
                "totalCurrentLiabilities": "165631000000",
                "currentAccountsPayable": "69860000000",
                "shortTermDebt": "22446000000",
                "totalNonCurrentLiabilities": "119877000000",
                "longTermDebt": "78328000000",
                "totalShareholderEquity": "73733000000",
                "retainedEarnings": "-14264000000",
                "commonStock": "93568000000",
                "commonStockSharesOutstanding": "15004697000"
            }
        ],
        "quarterlyReports": []
    }

@pytest.fixture
def sample_api_error() -> dict:
    return {"Error Message": "Invalid API call. Please retry or visit the documentation."}