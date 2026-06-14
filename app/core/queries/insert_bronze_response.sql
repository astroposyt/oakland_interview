INSERT INTO bronze_api_responses (api_called, ticker, status, response_json)
VALUES ($1, $2, $3, $4::jsonb);