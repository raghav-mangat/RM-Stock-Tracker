import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from models.database import db, Stock, Index, IndexHolding, StockMaster, StockMinute, StockHour, StockDay, StockWeek
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import fetch_all_stocks_data, fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES
from utils.datetime_utils import get_current_et, format_et_datetime, format_date
from utils.db_queries.all_stocks import get_top_stocks_categories, db_get_top_stocks_data
from pathlib import Path
import json
from email_scripts.send_watchlist_alerts import send_watchlist_alert_emails

# -------- Stage all new data --------
stocks_cache = {}  # ticker -> Stock object
stock_master_tickers = set()
new_stock_master = []
new_indices = []
new_index_holdings = []
new_stocks = []
new_chart_data = {timeframe: [] for timeframe in DB_TIMEFRAMES}

# ---- Helper to get Stock object (with chart data) ----
def get_or_fetch_stock(ticker, now_date):
    ticker_upper = ticker.upper()
    if ticker_upper in stocks_cache:
        return stocks_cache[ticker_upper]

    try:
        stock = fetch_stock_data(ticker, now_date)
        if stock:
            stocks_cache[ticker_upper] = stock
            new_stocks.append(stock)

            # Attach chart data via relationship
            for timeframe, data_list in new_chart_data.items():
                chart_records = fetch_chart_data(stock, timeframe, now_date)
                data_list.extend(chart_records)
        return stock
    except Exception as e:
        print(f"[Fetch Error] {ticker}: {e}")
        return None

def update_stock_master():
    # Delete dead stocks (those not in the new stock master tickers set)
    db.session.execute(
        delete(StockMaster).where(StockMaster.ticker.notin_(stock_master_tickers))
    )

    # Upsert stocks
    for stock in new_stock_master:
        existing = db.session.execute(
            db.select(StockMaster).where(StockMaster.ticker == stock.ticker)
        ).scalar()
        if existing:
            # Update fields
            for attr in stock.attribute_list():
                setattr(existing, attr, getattr(stock, attr))
        else:
            # Insert new stock
            db.session.add(stock)

def populate_db():
    """
    Populate the database by staging all data first, then replacing
    the main tables in a single atomic transaction.
    After the database is updated, compute Top Stocks and store them as well.
    """
    with app.app_context():
        print("Starting Database Population...\n")
        now = get_current_et()
        now_date = format_date(now)

        # ---- Stock Master ----
        stocks = fetch_all_stocks_data()
        for stock in stocks:
            ticker_upper = stock.ticker.upper()
            if ticker_upper not in stock_master_tickers:
                stock_master_tickers.add(ticker_upper)
                new_stock_master.append(stock)
            else:
                print(f"Duplicate ticker skipped: {stock.ticker}.")

        print(f"Skipped {len(stocks) - len(new_stock_master)} duplicate tickers.")
        print(f"Total of {len(new_stock_master)} stocks fetched from polygon API!")

        # ---- Indices and holdings ----
        print(f"Fetching data for indices...")
        for index in all_indices:
            index_info = get_index_info(index)
            index_obj = Index(
                name=index_info.get("name"),
                slug=index_info.get("slug"),
                url=index_info.get("url"),
                last_updated=now
            )
            new_indices.append(index_obj)

            holdings = fetch_index_data(index)
            for holding in holdings:
                ticker = holding.get("ticker")
                if ticker:
                    stock = get_or_fetch_stock(ticker, now_date)
                    if stock:
                        index_holding = IndexHolding(
                            index=index_obj,
                            stock=stock,
                            weight=holding.get("weight"),
                        )
                        new_index_holdings.append(index_holding)
            print(f"Fetched data for: {index}!")
        print(f"Fetched data for indices!")

        # -------- Transactional Replace --------
        try:
            print("\nUpdating the database with the new fetched data...")
            with db.session.begin():
                # Delete in FK-safe order
                db.session.execute(delete(IndexHolding))
                db.session.execute(delete(Index))
                db.session.execute(delete(StockMinute))
                db.session.execute(delete(StockHour))
                db.session.execute(delete(StockDay))
                db.session.execute(delete(StockWeek))
                db.session.execute(delete(Stock))

                update_stock_master()

                # Insert new data
                db.session.add_all(new_indices)
                db.session.add_all(new_stocks)
                for value in new_chart_data.values():
                    db.session.add_all(value)
                db.session.add_all(new_index_holdings)
            db.session.commit()

            save_populate_db_info(now)
            print("Updated the database with the new fetched data!\n")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

        print("Fetching Top Stocks data for updated database...")

        # Clearing the collected data to collect data for top stocks
        new_stocks.clear()
        for data_list in new_chart_data.values():
            data_list.clear()

        for category in get_top_stocks_categories().keys():
            for stocks_type in ["gainers", "losers", "top_traded"]:
                for stock in db_get_top_stocks_data(category, stocks_type):
                    ticker = stock.ticker
                    if ticker:
                        get_or_fetch_stock(ticker, now_date)

        print("Fetched Top Stocks data for updated database!")

        # Insert Top Stocks and their chart data
        print("Storing Top Stocks data in the database...")
        if new_stocks or any(new_chart_data.values()):
            db.session.add_all(new_stocks)
            for value in new_chart_data.values():
                db.session.add_all(value)
            db.session.commit()
        print("Stored Top Stocks data in the database!")

        db.session.close()
        print("\nDatabase Population Completed!\n")

def save_populate_db_info(now):
    # Define file path
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_file = data_dir / "populate_db_info.json"

    # Ensure folder exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Set current timestamp in US/Eastern
    timestamp = format_et_datetime(now)
    # Set current date
    date = format_date(now)

    # Prepare data
    populate_db_info = {
        "last_updated": timestamp,
        "last_updated_date": date
    }

    # Save to JSON
    with open(data_file, "w") as f:
        json.dump(populate_db_info, f, indent=2)

def main():
    # Load market status
    data_path = Path(__file__).resolve().parent.parent / "data" / "market_status.json"

    if data_path.exists():
        with open(data_path) as f:
            market_info = json.load(f)
            market_status = market_info.get("market_status")
        if market_status == "closed":
            print(f"Market status was {market_status} - skipping DB population!")
        else:
            print(f"Market status was {market_status} - proceeding with DB population...")
            populate_db()

            # Send watchlist alert emails to users after DB is populated
            send_watchlist_alert_emails()
    else:
        print("Market status file missing - cannot determine whether to proceed with DB population!")

if __name__ == "__main__":
    main()
