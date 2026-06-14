UPDATE dim_stocks 
SET last_balance_sheet_sync_at = CURRENT_TIMESTAMP 
WHERE ticker = $1;