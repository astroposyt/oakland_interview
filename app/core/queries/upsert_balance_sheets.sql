INSERT INTO fact_balance_sheets (
    stock_id, fiscal_date_ending, period_type, reported_currency, 
    total_assets, total_current_assets, cash_and_cash_equivalents, 
    cash_and_short_term_investments, inventory, current_net_receivables,
    total_non_current_assets, property_plant_equipment, accumulated_depreciation, 
    intangible_assets, goodwill, short_term_investments, total_liabilities, 
    total_current_liabilities, current_accounts_payable, short_term_debt, 
    total_non_current_liabilities, long_term_debt, total_shareholder_equity,
    retained_earnings, common_stock, shares_outstanding
)
VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
)
ON CONFLICT (stock_id, fiscal_date_ending, period_type) DO UPDATE SET
    reported_currency = EXCLUDED.reported_currency,
    total_assets = EXCLUDED.total_assets,
    total_current_assets = EXCLUDED.total_current_assets,
    cash_and_cash_equivalents = EXCLUDED.cash_and_cash_equivalents,
    cash_and_short_term_investments = EXCLUDED.cash_and_short_term_investments,
    inventory = EXCLUDED.inventory,
    current_net_receivables = EXCLUDED.current_net_receivables,
    total_non_current_assets = EXCLUDED.total_non_current_assets,
    property_plant_equipment = EXCLUDED.property_plant_equipment,
    accumulated_depreciation = EXCLUDED.accumulated_depreciation,
    intangible_assets = EXCLUDED.intangible_assets,
    goodwill = EXCLUDED.goodwill,
    short_term_investments = EXCLUDED.short_term_investments,
    total_liabilities = EXCLUDED.total_liabilities,
    total_current_liabilities = EXCLUDED.total_current_liabilities,
    current_accounts_payable = EXCLUDED.current_accounts_payable,
    short_term_debt = EXCLUDED.short_term_debt,
    total_non_current_liabilities = EXCLUDED.total_non_current_liabilities,
    long_term_debt = EXCLUDED.long_term_debt,
    total_shareholder_equity = EXCLUDED.total_shareholder_equity,
    retained_earnings = EXCLUDED.retained_earnings,
    common_stock = EXCLUDED.common_stock,
    shares_outstanding = EXCLUDED.shares_outstanding;