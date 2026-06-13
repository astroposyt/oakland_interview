UPDATE dim_stocks
SET should_fetch = FALSE
WHERE ticker = $1;