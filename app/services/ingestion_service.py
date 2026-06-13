from pydantic import ValidationError
from app.core.api_client import get_api_client
from app.core.logger import get_logger
from app.schemas.prices import AlphaVantagePriceParser
from app.repositories.bronze_repo import BronzeRepository
from app.repositories.silver_repo import SilverRepository
from app.schemas.balance_sheets import AlphaVantageBalanceParser

logger = get_logger(__name__)

class StockIngestionService:
    """Business logic for orchestrating API -> Bronze -> Silver -> Gold."""

    @staticmethod
    async def process_daily_prices(ticker: str) -> dict:
        logger.info(f"Starting daily price pipeline for {ticker}")
        client = get_api_client()
        
        raw_data = await client.fetch_stock_data(ticker)
        
        is_error = any(key in raw_data for key in ["Error Message", "Information", "Note"])
        status = "ERROR" if is_error else "SUCCESS"
        
        await BronzeRepository.insert_response("TIME_SERIES_DAILY", ticker, status, raw_data)
        
        if status == "ERROR":
            logger.warning(f"API Error/Rate Limit for {ticker}. Halting pipeline.")
            return raw_data

        try:
            parsed_data = AlphaVantagePriceParser.model_validate(raw_data)
        except ValidationError as e:
            logger.error(f"Schema validation failed for {ticker}: {e}")
            raise ValueError(f"Data schema changed or invalid for {ticker}")
            
        # 5. Upsert to Silver
        await SilverRepository.upsert_prices(ticker, parsed_data.records)
        
        logger.info(f"Successfully processed prices for {ticker}")
        return raw_data
    

    @staticmethod
    async def process_balance_sheets(ticker: str) -> dict:
        logger.info(f"Starting balance sheet pipeline for {ticker}")
        client = get_api_client()
        
        raw_data = await client.fetch_balance_sheet_data(ticker)

        is_error = any(key in raw_data for key in ["Error Message", "Information", "Note"])
        status = "ERROR" if is_error else "SUCCESS"

        await BronzeRepository.insert_response("BALANCE_SHEET", ticker, status, raw_data)
        
        if status == "ERROR":
            logger.warning(f"API Error/Rate Limit for {ticker} balance sheets. Halting pipeline.")
            return raw_data
        try:
            parsed_data = AlphaVantageBalanceParser.model_validate(raw_data)
        except ValidationError as e:
            logger.error(f"Schema validation failed for {ticker} balance sheets: {e}")
            raise ValueError(f"Data schema changed or invalid for {ticker}")
            
        await SilverRepository.upsert_balance_sheets(ticker, parsed_data.annual_reports, "Annual")
        await SilverRepository.upsert_balance_sheets(ticker, parsed_data.quarterly_reports, "Quarterly")
        
        logger.info(f"Successfully processed balance sheets for {ticker}")
        return raw_data