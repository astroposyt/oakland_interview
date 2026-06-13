WITH ranked_prices AS (
    SELECT 
        s.ticker,
        p.price_date,
        p.high_price,
        p.close_price,
        p.volume,
        ROW_NUMBER() OVER (PARTITION BY p.stock_id ORDER BY p.high_price DESC) as rn
    FROM fact_daily_prices p
    JOIN dim_stocks s ON p.stock_id = s.id
    WHERE ($1::VARCHAR IS NULL OR s.ticker = $1)
)
SELECT ticker, price_date, high_price, close_price, volume
FROM ranked_prices
WHERE rn = 1
ORDER BY high_price DESC;