import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.scheduler import sync_daily_prices, sync_balance_sheets

@pytest.mark.asyncio
@patch("app.core.scheduler.StockRepository.fetch_stocks_needing_price_sync")
@patch("app.core.scheduler.StockIngestionService.process_daily_prices")
@patch("app.core.scheduler.StockRepository.update_price_sync_time")
@patch("app.core.scheduler.GoldRepository.refresh_materialized_views")
@patch("app.core.scheduler.ping_deadmans_switch")
async def test_sync_daily_prices_skips_when_already_synced_today(
    mock_ping, mock_refresh, mock_update_time, mock_process, mock_fetch_needing
):
    """Verifies that if all stocks are already synced today, no API calls are made."""

    mock_fetch_needing.return_value = []

    await sync_daily_prices()

    mock_fetch_needing.assert_called_once()
    mock_process.assert_not_called()         
    mock_update_time.assert_not_called()     
    mock_refresh.assert_not_called()         
    mock_ping.assert_called_once()           


@pytest.mark.asyncio
@patch("app.core.scheduler.StockRepository.fetch_stocks_needing_price_sync")
@patch("app.core.scheduler.StockIngestionService.process_daily_prices")
@patch("app.core.scheduler.StockRepository.update_price_sync_time")
@patch("app.core.scheduler.GoldRepository.refresh_materialized_views")
@patch("app.core.scheduler.ping_deadmans_switch")
async def test_sync_daily_prices_runs_only_for_outdated_stocks(
    mock_ping, mock_refresh, mock_update_time, mock_process, mock_fetch_needing
):
    """Verifies that the sync engine executes and updates state only for outdated tickers."""
 
    mock_fetch_needing.return_value = [{"ticker": "AAPL", "company_name": "Apple Inc"}]
    mock_process.return_value = {"Meta Data": {"2. Symbol": "AAPL"}}

    await sync_daily_prices()


    mock_process.assert_called_once_with("AAPL")     
    mock_update_time.assert_called_once_with("AAPL")  
    mock_refresh.assert_called_once()                