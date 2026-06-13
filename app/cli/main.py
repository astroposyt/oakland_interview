import argparse
import asyncio
import sys
from typing import Any
from app.core.database import (
    add_tracked_stock, 
    untrack_stock,
    fetch_tracked_stocks, 
    fetch_recent_prices, 
    fetch_recent_balance_sheets, 
    fetch_max_price_days
)
from app.core.actions import extract_stock_pipeline, extract_balance_sheet_pipeline

def print_table(headers: list[str], data: list[list[Any]]) -> None:
    if not data:
        print("No records found.")
        return
    col_widths = [max(len(str(val)) for val in col) for col in zip(headers, *data)]
    format_str = " | ".join(f"{{:<{w}}}" for w in col_widths)
    print(format_str.format(*headers))
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
    for row in data:
        print(format_str.format(*[str(item) for item in row]))

async def handle_add(args):
    print(f"Registering ticker {args.ticker.upper()}...")
    await add_tracked_stock(args.ticker, args.name)
    print(f"Successfully tracking {args.ticker.upper()}.")

async def handle_untrack(args):
    print(f"Stopping sync execution tracing for ticker {args.ticker.upper()}...")
    await untrack_stock(args.ticker)
    print(f"Ticker {args.ticker.upper()} is no longer monitored.")

async def handle_sync(args):
    stocks = await fetch_tracked_stocks()
    if not stocks:
        print("No active monitored stocks found in database.")
        return
    print(f"Beginning pipeline synchronization for {len(stocks)} stocks...")
    for stock in stocks:
        ticker = stock["ticker"]
        print(f"[{ticker}] Running sync...")
        await extract_stock_pipeline(ticker)
        await extract_balance_sheet_pipeline(ticker)
    print("Synchronization complete.")

async def handle_gold(args):
    if args.type == "prices":
        records = await fetch_recent_prices(per_stock_limit=args.limit)
        headers = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]
        rows = [[r["ticker"], r["price_date"], r["open_price"], r["high_price"], r["low_price"], r["close_price"], r["volume"]] for r in records]
        print_table(headers, rows)
    elif args.type == "balance":
        records = await fetch_recent_balance_sheets("Annual", per_stock_limit=args.limit)
        headers = ["Ticker", "Period", "Date", "Currency", "Assets", "Liabilities", "Equity"]
        rows = [[r["ticker"], r["period_type"], r["fiscal_date_ending"], r["reported_currency"], r["total_assets"], r["total_liabilities"], r["total_shareholder_equity"]] for r in records]
        print_table(headers, rows)

async def handle_max_day(args):
    records = await fetch_max_price_days(ticker=args.ticker)
    headers = ["Ticker", "Max Price Date", "Highest Price (All-Time)", "Close Price", "Volume"]
    rows = [[r["ticker"], r["price_date"], r["high_price"], r["close_price"], r["volume"]] for r in records]
    print_table(headers, rows)

def main():
    parser = argparse.ArgumentParser(description="Oakland Financial Data Lake Platform CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Register a new stock ticker to track")
    add_parser.add_argument("--ticker", "-t", required=True, help="Stock ticker symbol (e.g. AAPL)")
    add_parser.add_argument("--name", "-n", required=True, help="Full corporate name")

    untrack_parser = subparsers.add_parser("untrack", help="Remove a stock ticker from monitored synchronizations")
    untrack_parser.add_argument("--ticker", "-t", required=True, help="Stock ticker symbol")

    subparsers.add_parser("sync", help="Execute ETL pipelines for monitored stocks")

    gold_parser = subparsers.add_parser("gold", help="View chronological historical data from fact tables")
    gold_parser.add_argument("--type", choices=["prices", "balance"], default="prices", help="Dataset type to inspect")
    gold_parser.add_argument("--limit", "-l", type=int, default=3, help="Number of records *per stock* to return")

    max_parser = subparsers.add_parser("max-day", help="Get the highest peak transaction price record")
    max_parser.add_argument("--ticker", "-t", default=None, help="Optional specific stock ticker to search")

    args = parser.parse_args()
    command_map = {
        "add": handle_add,
        "untrack": handle_untrack,
        "sync": handle_sync,
        "gold": handle_gold,
        "max-day": handle_max_day
    }
    asyncio.run(command_map[args.command](args))

if __name__ == "__main__":
    main()