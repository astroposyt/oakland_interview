WITH inserted AS (
    INSERT INTO dim_stocks (ticker, company_name)
    VALUES ($1, $2)
    ON CONFLICT (ticker) DO NOTHING
    RETURNING id
)
SELECT id FROM inserted
UNION ALL
SELECT id FROM dim_stocks WHERE ticker = $1;