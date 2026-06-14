UPDATE dim_stocks 
SET last_price_sync_at = CURRENT_TIMESTAMP 
WHERE ticker = $1;