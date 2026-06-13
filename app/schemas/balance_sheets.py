from pydantic import BaseModel, model_validator, Field
from datetime import date
from typing import Optional, List

class BalanceSheetRecord(BaseModel):
    fiscal_date_ending: date = Field(alias="fiscalDateEnding")
    reported_currency: str = Field(alias="reportedCurrency")
    total_assets: Optional[int] = Field(None, alias="totalAssets")
    total_current_assets: Optional[int] = Field(None, alias="totalCurrentAssets")
    cash_and_cash_equivalents: Optional[int] = Field(None, alias="cashAndCashEquivalentsAtCarryingValue")
    cash_and_short_term_investments: Optional[int] = Field(None, alias="cashAndShortTermInvestments")
    inventory: Optional[int] = Field(None, alias="inventory")
    current_net_receivables: Optional[int] = Field(None, alias="currentNetReceivables")
    total_non_current_assets: Optional[int] = Field(None, alias="totalNonCurrentAssets")
    property_plant_equipment: Optional[int] = Field(None, alias="propertyPlantEquipment")
    accumulated_depreciation: Optional[int] = Field(None, alias="accumulatedDepreciationAmortizationPPE")
    intangible_assets: Optional[int] = Field(None, alias="intangibleAssets")
    goodwill: Optional[int] = Field(None, alias="goodwill")
    short_term_investments: Optional[int] = Field(None, alias="shortTermInvestments")
    total_liabilities: Optional[int] = Field(None, alias="totalLiabilities")
    total_current_liabilities: Optional[int] = Field(None, alias="totalCurrentLiabilities")
    current_accounts_payable: Optional[int] = Field(None, alias="currentAccountsPayable")
    short_term_debt: Optional[int] = Field(None, alias="shortTermDebt")
    total_non_current_liabilities: Optional[int] = Field(None, alias="totalNonCurrentLiabilities")
    long_term_debt: Optional[int] = Field(None, alias="longTermDebt")
    total_shareholder_equity: Optional[int] = Field(None, alias="totalShareholderEquity")
    retained_earnings: Optional[int] = Field(None, alias="retainedEarnings")
    common_stock: Optional[int] = Field(None, alias="commonStock")
    shares_outstanding: Optional[int] = Field(None, alias="commonStockSharesOutstanding")

    @model_validator(mode="before")
    @classmethod
    def clean_none_strings(cls, data: dict) -> dict:
        for key, val in data.items():
            if val == "None":
                data[key] = None
        return data

class AlphaVantageBalanceParser(BaseModel):
    annual_reports: List[BalanceSheetRecord]
    quarterly_reports: List[BalanceSheetRecord]

    @model_validator(mode="before")
    @classmethod
    def extract_reports(cls, data: dict) -> dict:
        return {
            "annual_reports": data.get("annualReports", []),
            "quarterly_reports": data.get("quarterlyReports", [])
        }