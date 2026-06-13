from unittest.mock import patch, AsyncMock

def test_add_stock_endpoint_success(client):
    with patch("app.api.routers.api_v1.StockRepository.add_tracked_stock", new_callable=AsyncMock) as mock_add, \
         patch("app.api.routers.api_v1.StockIngestionService.process_daily_prices", new_callable=AsyncMock) as mock_prices, \
         patch("app.api.routers.api_v1.StockIngestionService.process_balance_sheets", new_callable=AsyncMock) as mock_balances, \
         patch("app.api.routers.api_v1.GoldRepository.refresh_materialized_views", new_callable=AsyncMock) as mock_refresh:
        
        response = client.post(
            "/api/v1/control/stocks",
            json={"ticker": "MSFT", "company_name": "Microsoft"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "MSFT added and data fetched."}
        
        mock_add.assert_called_once_with("MSFT", "Microsoft")
        mock_prices.assert_called_once_with("MSFT")
        mock_refresh.assert_called_once()


def test_extract_stock_data_handles_429_rate_limit(client):
    # Mock the service to return the Alpha Vantage error payload
    with patch("app.api.routers.api_v1.StockIngestionService.process_daily_prices", new_callable=AsyncMock) as mock_service:
        mock_service.return_value = {"Error Message": "Rate limit exceeded"}
        
        response = client.get("/api/v1/prices/AAPL")
        
        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limit exceeded"


def test_extract_stock_data_handles_422_validation_error(client):
    # Mock the service to raise the ValueError from Pydantic failures
    with patch("app.api.routers.api_v1.StockIngestionService.process_daily_prices", new_callable=AsyncMock) as mock_service:
        mock_service.side_effect = ValueError("Data schema changed")
        
        response = client.get("/api/v1/prices/AAPL")
        
        assert response.status_code == 422
        assert response.json()["detail"] == "Data schema changed"