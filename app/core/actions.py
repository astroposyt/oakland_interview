from app.core.api_client import get_api_client

async def extract_stock_pipeline(ticker: str) -> dict:
    client = get_api_client()
    return await client.fetch_stock_data(ticker)

async def extract_balance_sheet_pipeline(ticker: str) -> dict:
    client = get_api_client()
    return await client.fetch_balance_sheet_data(ticker)