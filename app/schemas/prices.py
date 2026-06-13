from pydantic import BaseModel, model_validator
from datetime import date
from decimal import Decimal
from typing import List

class DailyPriceRecord(BaseModel):
    price_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int

class AlphaVantagePriceParser(BaseModel):
    records: List[DailyPriceRecord]

    @model_validator(mode="before")
    @classmethod
    def transform_raw_data(cls, data: dict) -> dict:
        time_series = data.get("Time Series (Daily)", {})
        parsed_records = []
        for date_str, metrics in time_series.items():
            parsed_records.append({
                "price_date": date_str,
                "open_price": metrics.get("1. open"),
                "high_price": metrics.get("2. high"),
                "low_price": metrics.get("3. low"),
                "close_price": metrics.get("4. close"),
                "volume": metrics.get("5. volume")
            })
        return {"records": parsed_records}