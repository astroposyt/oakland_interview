from pydantic import ValidationError
from app.core.api_client import get_api_client
from app.core.logger import get_logger
from app.schemas.prices import AlphaVantagePriceParser
from app.repositories.bronze_repo import BronzeRepository
from app.repositories.silver_repo import SilverRepository
from app.schemas.balance_sheets import AlphaVantageBalanceParser, BalanceSheetRecord
from app.schemas.prices import DailyPriceRecord

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
            return raw_data

        time_series = raw_data.get("Time Series (Daily)", {})
        valid_records = []
        corrupted_records_count = 0

        for date_str, metrics in time_series.items():
            try:
                record = DailyPriceRecord(
                    price_date=date_str,
                    open_price=metrics.get("1. open"),
                    high_price=metrics.get("2. high"),
                    low_price=metrics.get("3. low"),
                    close_price=metrics.get("4. close"),
                    volume=metrics.get("5. volume")
                )
                valid_records.append(record)
            except (ValidationError, ValueError) as row_err:
                corrupted_records_count += 1
                # In production, you would write this row into a dead_letter_queue table here.
                logger.warning(f"[DLQ][{ticker}] Isolated a corrupt data row on date {date_str}: {str(row_err)}")
                continue
        if valid_records:
            await SilverRepository.upsert_prices(ticker, valid_records)
            logger.info(f"Loaded {len(valid_records)} clean rows for {ticker}. Skipped {corrupted_records_count} bad rows.")
        else:
            logger.error(f"Pipeline failed completely for {ticker}: No rows passed validation constraints.")
            raise ValueError("Data schema changed or invalid")

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

        corrupted_rows = 0
        
        clean_annual_reports = []
        for report in raw_data.get("annualReports", []):
            try:
                parsed_report = BalanceSheetRecord.model_validate(report)
                clean_annual_reports.append(parsed_report)
            except (ValidationError, ValueError) as row_err:
                corrupted_rows += 1
                logger.warning(f"[DLQ][{ticker}][Annual] Quarantined historic statement on date {report.get('fiscalDateEnding')}: {str(row_err)}")
                continue

        clean_quarterly_reports = []
        for report in raw_data.get("quarterlyReports", []):
            try:
                parsed_report = BalanceSheetRecord.model_validate(report)
                clean_quarterly_reports.append(parsed_report)
            except (ValidationError, ValueError) as row_err:
                corrupted_rows += 1
                logger.warning(f"[DLQ][{ticker}][Quarterly] Quarantined historic statement on date {report.get('fiscalDateEnding')}: {str(row_err)}")
                continue

        if clean_annual_reports:
            await SilverRepository.upsert_balance_sheets(ticker, clean_annual_reports, "Annual")
        if clean_quarterly_reports:
            await SilverRepository.upsert_balance_sheets(ticker, clean_quarterly_reports, "Quarterly")

        logger.info(
            f"Successfully processed balance sheets for {ticker}. "
            f"Loaded {len(clean_annual_reports)} Annual and {len(clean_quarterly_reports)} Quarterly records. "
            f"Quarantined {corrupted_rows} corrupt rows to DLQ logging context."
        )
        return raw_data