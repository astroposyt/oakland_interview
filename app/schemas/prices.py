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

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "DailyPriceRecord":

        if any(p <= 0 for p in [self.open_price, self.high_price, self.low_price, self.close_price]):
            raise ValueError("Data QA Alert: Trading prices must be strictly positive.")
        if self.volume < 0:
            raise ValueError("Data QA Alert: Traded volume cannot be negative.")
        
        if self.low_price > self.high_price:
            raise ValueError("Data QA Alert: Low trading bounds cannot exceed high boundaries.")
        return self

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