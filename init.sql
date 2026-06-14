CREATE TABLE IF NOT EXISTS bronze_api_responses (
    id SERIAL PRIMARY KEY,
    api_called VARCHAR(50) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_json JSONB NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    should_fetch BOOLEAN DEFAULT TRUE,
    last_price_sync_at TIMESTAMP WITH TIME ZONE,
    last_balance_sheet_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_daily_prices (
    stock_id INT REFERENCES dim_stocks(id) ON DELETE CASCADE,
    price_date DATE NOT NULL,
    open_price NUMERIC(12, 4) NOT NULL,
    high_price NUMERIC(12, 4) NOT NULL,
    low_price NUMERIC(12, 4) NOT NULL,
    close_price NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (stock_id, price_date)
);

CREATE TABLE IF NOT EXISTS fact_balance_sheets (
    stock_id INT REFERENCES dim_stocks(id) ON DELETE CASCADE,
    fiscal_date_ending DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    reported_currency VARCHAR(10),
    total_assets BIGINT,
    total_current_assets BIGINT,
    cash_and_cash_equivalents BIGINT,
    cash_and_short_term_investments BIGINT,
    inventory BIGINT,
    current_net_receivables BIGINT,
    total_non_current_assets BIGINT,
    property_plant_equipment BIGINT,
    accumulated_depreciation BIGINT,
    intangible_assets BIGINT,
    goodwill BIGINT,
    short_term_investments BIGINT,
    total_liabilities BIGINT,
    total_current_liabilities BIGINT,
    current_accounts_payable BIGINT,
    short_term_debt BIGINT,
    total_non_current_liabilities BIGINT,
    long_term_debt BIGINT,
    total_shareholder_equity BIGINT,
    retained_earnings BIGINT,
    common_stock BIGINT,
    shares_outstanding BIGINT,
    PRIMARY KEY (stock_id, fiscal_date_ending, period_type)
);

CREATE MATERIALIZED VIEW gold_latest_daily_prices AS
WITH ranked_prices AS (
    SELECT 
        s.ticker,
        s.company_name,
        p.price_date,
        p.open_price,
        p.high_price,
        p.low_price,
        p.close_price,
        p.volume,
        ROW_NUMBER() OVER (PARTITION BY p.stock_id ORDER BY p.price_date DESC) as rn
    FROM fact_daily_prices p
    JOIN dim_stocks s ON p.stock_id = s.id
)
SELECT 
    ticker,
    company_name,
    price_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM ranked_prices
WHERE rn = 1;

CREATE MATERIALIZED VIEW gold_latest_balance_sheets AS
WITH ranked_balances AS (
    SELECT 
        s.ticker,
        s.company_name,
        b.*,
        ROW_NUMBER() OVER (PARTITION BY b.stock_id, b.period_type ORDER BY b.fiscal_date_ending DESC) as rn
    FROM fact_balance_sheets b
    JOIN dim_stocks s ON b.stock_id = s.id
)
SELECT 
    ticker,
    company_name,
    fiscal_date_ending,
    period_type,
    reported_currency,
    total_assets,
    total_liabilities,
    total_shareholder_equity,
    retained_earnings,
    shares_outstanding
FROM ranked_balances
WHERE rn = 1;

CREATE UNIQUE INDEX idx_gold_prices_ticker ON gold_latest_daily_prices (ticker);
CREATE UNIQUE INDEX idx_gold_balance_ticker ON gold_latest_balance_sheets (ticker, period_type);