INSERT INTO fact_daily_prices (stock_id, price_date, open_price, high_price, low_price, close_price, volume)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (stock_id, price_date) DO UPDATE SET
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume;