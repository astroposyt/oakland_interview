SELECT ticker, company_name 
FROM dim_stocks 
WHERE should_fetch = TRUE 
  AND (last_balance_sheet_sync_at IS NULL OR DATE(last_balance_sheet_sync_at AT TIME ZONE 'UTC') < CURRENT_DATE);