import os
import asyncio
import typer
from rich.console import Console
from rich.table import Table

# Import our layered architecture
from app.repositories.stock_repo import StockRepository
from app.repositories.gold_repo import GoldRepository
from app.services.ingestion_service import StockIngestionService
from app.core.db import init_db_pool, close_db_pool

app = typer.Typer(help="Oakland Data Lake CLI")
console = Console()

FEATURE_CLI_SYNC = os.getenv("ENABLE_CLI_SYNC", "false").lower() == "true"

def run_async(coro):
    async def _wrapper():
        await init_db_pool()
        try:
            await coro
        finally:
            await close_db_pool()
    return asyncio.run(_wrapper())


def run_async(coro):
    """Helper to run async functions in synchronous Typer commands."""
    return asyncio.run(coro)

@app.command("add")
def add_stock(ticker: str = typer.Option(..., "-t", help="Stock ticker symbol"), 
              name: str = typer.Option(..., "-n", help="Full corporate name")):
    """Register a new stock ticker to track."""
    async def _add():
        await StockRepository.add_tracked_stock(ticker, name)
        console.print(f"[bold green]Successfully tracking {ticker.upper()}.[/bold green]")
    run_async(_add())

@app.command("untrack")
def untrack_stock(ticker: str = typer.Option(..., "-t", help="Stock ticker symbol")):
    """Remove a stock ticker from monitored synchronizations."""
    async def _untrack():
        await StockRepository.untrack_stock(ticker)
        console.print(f"[bold yellow]Ticker {ticker.upper()} is no longer monitored.[/bold yellow]")
    run_async(_untrack())

@app.command("sync")
def sync_pipelines():
    """Execute ETL pipelines for all monitored stocks (Gated by Feature Flag)."""

    if not FEATURE_CLI_SYNC:
        console.print("\n[bold red]🚫 Access Denied[/bold red]")
        console.print("[yellow]The 'sync' feature is currently deactivated via configuration feature flags.[/yellow]")
        console.print("To activate this pipeline engine, update [bold].env[/bold] to: [green]ENABLE_CLI_SYNC=true[/green]\n")
        raise typer.Exit(code=1)

    async def _sync():
        stocks = await StockRepository.fetch_tracked_stocks()
        if not stocks:
            console.print("[bold red]No active monitored stocks found.[/bold red]")
            return
            
        with console.status(f"[bold blue]Syncing {len(stocks)} stocks..."):
            for stock in stocks:
                ticker = stock["ticker"]
                await StockIngestionService.process_daily_prices(ticker)
                await StockIngestionService.process_balance_sheets(ticker)
            
            await GoldRepository.refresh_materialized_views()
        console.print("[bold green]Synchronization complete.[/bold green]")
    run_async(_sync())

@app.command("prices")
def view_prices(limit: int = typer.Option(5, "-l", help="Number of records to return")):
    """View chronological historical data from Gold tables."""
    async def _view():
        records = await GoldRepository.fetch_recent_prices(limit)
        
        table = Table("Ticker", "Date", "Open", "High", "Low", "Close", "Volume", title="Recent Prices")
        for r in records:
            table.add_row(r["ticker"], str(r["price_date"]), str(r["open_price"]), 
                          str(r["high_price"]), str(r["low_price"]), str(r["close_price"]), str(r["volume"]))
        console.print(table)
    run_async(_view())

if __name__ == "__main__":
    app()