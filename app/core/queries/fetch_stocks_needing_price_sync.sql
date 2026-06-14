SELECT ticker, company_name 
FROM dim_stocks 
WHERE should_fetch = TRUE 
  AND (last_price_sync_at IS NULL OR DATE(last_price_sync_at AT TIME ZONE 'UTC') < CURRENT_DATE);