import logging
from typing import Callable, Any, Type
from pydantic import BaseModel, ValidationError
from app.core.api_client import get_api_client
from app.core.database import insert_bronze_response, upsert_silver_prices, upsert_silver_balance_sheets
from app.schemas.prices import AlphaVantagePriceParser
from app.schemas.balance_sheets import AlphaVantageBalanceParser

logger = logging.getLogger("uvicorn.error")

async def _orchestrate_pipeline(
    ticker: str,
    api_called: str,
    fetch_handler: Callable[[str], Any],
    parser_model: Type[BaseModel],
    silver_handler: Callable[[Any], Any]
) -> dict:
    raw_data = await fetch_handler(ticker)
    
    status = "ERROR" if "Error Message" in raw_data else "SUCCESS"
    await insert_bronze_response(api_called, ticker, status, raw_data)
    
    if status == "ERROR":
        return raw_data

    try:
        parsed_data = parser_model.model_validate(raw_data)
    except ValidationError as e:
        logger.error(f"Pydantic validation failed for {ticker} {api_called}: {e.json()}")
        raise ValueError(f"Data validation failure encountered for ticker {ticker}")
        
    await silver_handler(parsed_data)
    return raw_data

async def extract_stock_pipeline(ticker: str) -> dict:
    client = get_api_client()
    
    async def save_to_silver(parsed):
        await upsert_silver_prices(ticker, parsed.records)
        
    return await _orchestrate_pipeline(
        ticker=ticker,
        api_called="TIME_SERIES_DAILY",
        fetch_handler=client.fetch_stock_data,
        parser_model=AlphaVantagePriceParser,
        silver_handler=save_to_silver
    )

async def extract_balance_sheet_pipeline(ticker: str) -> dict:
    client = get_api_client()
    
    async def save_to_silver(parsed):
        await upsert_silver_balance_sheets(ticker, parsed.annual_reports, "Annual")
        await upsert_silver_balance_sheets(ticker, parsed.quarterly_reports, "Quarterly")
        
    return await _orchestrate_pipeline(
        ticker=ticker,
        api_called="BALANCE_SHEET",
        fetch_handler=client.fetch_balance_sheet_data,
        parser_model=AlphaVantageBalanceParser,
        silver_handler=save_to_silver
    )