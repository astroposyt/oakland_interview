WITH ranked_prices AS (
    SELECT 
        s.ticker, 
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
SELECT ticker, price_date, open_price, high_price, low_price, close_price, volume
FROM ranked_prices
WHERE rn <= $1
ORDER BY ticker ASC, price_date DESC;