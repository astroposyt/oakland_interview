INSERT INTO dim_stocks (ticker, company_name, should_fetch)
VALUES ($1, $2, TRUE)
ON CONFLICT (ticker) DO UPDATE SET 
    should_fetch = TRUE,
    company_name = EXCLUDED.company_name;