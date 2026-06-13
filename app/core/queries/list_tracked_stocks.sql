SELECT ticker, company_name, should_fetch 
FROM dim_stocks 
WHERE should_fetch = TRUE;