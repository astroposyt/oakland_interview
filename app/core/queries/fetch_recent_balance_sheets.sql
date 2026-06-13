WITH ranked_sheets AS (
    SELECT 
        s.ticker, 
        b.period_type, 
        b.fiscal_date_ending, 
        b.reported_currency, 
        b.total_assets, 
        b.total_liabilities, 
        b.total_shareholder_equity,
        ROW_NUMBER() OVER (PARTITION BY b.stock_id ORDER BY b.fiscal_date_ending DESC) as rn
    FROM fact_balance_sheets b
    JOIN dim_stocks s ON b.stock_id = s.id
    WHERE b.period_type = $1
)
SELECT ticker, period_type, fiscal_date_ending, reported_currency, total_assets, total_liabilities, total_shareholder_equity
FROM ranked_sheets
WHERE rn <= $2
ORDER BY ticker ASC, fiscal_date_ending DESC;