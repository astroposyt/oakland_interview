import os
import json
import httpx
from abc import ABC, abstractmethod

class StockApiClient(ABC):
    @abstractmethod
    async def fetch_stock_data(self, ticker: str) -> dict:
        pass

    @abstractmethod
    async def fetch_balance_sheet_data(self, ticker: str) -> dict:
        pass

class RealAlphaVantageClient(StockApiClient):
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    async def fetch_stock_data(self, ticker: str) -> dict:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker.upper(),
            "apikey": self.api_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()

    async def fetch_balance_sheet_data(self, ticker: str) -> dict:
        params = {
            "function": "BALANCE_SHEET",
            "symbol": ticker.upper(),
            "apikey": self.api_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()

class MockAlphaVantageClient(StockApiClient):
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

    async def fetch_stock_data(self, ticker: str) -> dict:
        normalized_ticker = ticker.upper()
        ticker_file_map = {
            "AAPL": "apple_daily.json",
            "IBM": "ibm_daily.json"
        }
        filename = ticker_file_map.get(normalized_ticker, "apple_daily.json")
        file_path = os.path.join(self.current_dir, "mock_data", filename)
        return self._load_json_file(file_path, normalized_ticker)

    async def fetch_balance_sheet_data(self, ticker: str) -> dict:
        normalized_ticker = ticker.upper()
        ticker_file_map = {
            "IBM": "ibm_balance.json",
            "AAPL": "apple_balance.json",
        }
        filename = ticker_file_map.get(normalized_ticker, "ibm_balance.json")
        file_path = os.path.join(self.current_dir, "mock_data", filename)
        return self._load_json_file(file_path, normalized_ticker)

    def _load_json_file(self, file_path: str, ticker: str) -> dict:
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
            if "symbol" in data:
                data["symbol"] = ticker
            elif "Meta Data" in data and "2. Symbol" in data["Meta Data"]:
                data["Meta Data"]["2. Symbol"] = ticker
            return data
        except FileNotFoundError:
            return {"Error Message": f"Mock data file not found at {file_path}"}

def get_api_client() -> StockApiClient:
    use_mock = os.getenv("USE_MOCK_API", "false").lower() == "true"
    if use_mock:
        return MockAlphaVantageClient()
    return RealAlphaVantageClient()