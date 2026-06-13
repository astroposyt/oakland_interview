import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from app.schemas.prices import AlphaVantagePriceParser
from app.schemas.balance_sheets import AlphaVantageBalanceParser

def test_price_parser_conversion(sample_raw_price_data):
    parsed = AlphaVantagePriceParser.model_validate(sample_raw_price_data)
    assert len(parsed.records) == 1
    
    record = parsed.records[0]
    assert record.price_date == date(2026, 6, 12)
    assert isinstance(record.open_price, Decimal)
    assert record.open_price == Decimal("296.0300")
    assert record.volume == 38784789

def test_price_parser_crashing_on_corrupt_types():
    corrupt_data = {
        "Time Series (Daily)": {
            "2026-06-12": {
                "1. open": "NOT_A_NUMBER",
                "2. high": "297.1400",
                "3. low": "289.6200",
                "4. close": "291.1300",
                "5. volume": "38784789"
            }
        }
    }
    with pytest.raises(ValidationError):
        AlphaVantagePriceParser.model_validate(corrupt_data)

def test_price_parser_handles_empty_time_series():
    empty_data = {"Time Series (Daily)": {}}
    parsed = AlphaVantagePriceParser.model_validate(empty_data)
    assert len(parsed.records) == 0

def test_balance_sheet_aliasing_and_none_scrubbing(sample_raw_balance_sheet):
    parsed = AlphaVantageBalanceParser.model_validate(sample_raw_balance_sheet)
    assert len(parsed.annual_reports) == 1
    
    report = parsed.annual_reports[0]
    assert report.fiscal_date_ending == date(2025, 9, 30)
    assert report.total_assets == 359241000000
    assert report.accumulated_depreciation is None
    assert report.goodwill is None

def test_balance_sheet_parser_handles_missing_report_keys():
    broken_payload = {"symbol": "AAPL"}
    parsed = AlphaVantageBalanceParser.model_validate(broken_payload)
    assert len(parsed.annual_reports) == 0
    assert len(parsed.quarterly_reports) == 0