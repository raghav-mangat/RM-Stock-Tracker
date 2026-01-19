import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from models.database import db, Stock, Index, IndexHolding, StockMaster, StockMinute, StockHour, StockDay, StockWeek
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import fetch_all_stocks_data, fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES
from utils.datetime_utils import get_current_utc, format_dt_et, format_date
from utils.db_queries.stock_master_data import get_all_stock_master
from utils.db_queries.all_stocks import get_top_stocks_categories, db_get_top_stocks_data
from utils.db_queries.query_stocks import get_query_stocks
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

stocks_cache.clear()
stock_master_tickers.clear()
new_stock_master.clear()
new_indices.clear()
new_index_holdings.clear()
new_stocks.clear()
for v in new_chart_data.values():
    v.clear()

# ---- Helper to get Stock object (with chart data) ----
def get_or_fetch_stock(ticker, now_date, stock_master_map):
    if ticker in stocks_cache:
        return stocks_cache[ticker]

    try:
        stock = fetch_stock_data(ticker, now_date, stock_master_map.get(ticker, None))
        if stock:
            stocks_cache[ticker] = stock
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

def clear_stocks_data():
    new_stocks.clear()
    for data_list in new_chart_data.values():
        data_list.clear()

def add_new_stocks_data():
    if new_stocks or any(new_chart_data.values()):
        db.session.add_all(new_stocks)
        for value in new_chart_data.values():
            db.session.add_all(value)
        db.session.flush()

def populate_db():
    """
    Populate the database by staging all data first, then replacing
    the main tables in a single atomic transaction.
    """
    with app.app_context():
        print("Starting Database Population...\n")
        now = get_current_utc()
        now_date = format_date(now)

        try:
            with db.session.begin():
                print("Deleting Tables...")
                # Delete in FK-safe order
                db.session.execute(delete(IndexHolding))
                db.session.execute(delete(Index))
                db.session.execute(delete(StockMinute))
                db.session.execute(delete(StockHour))
                db.session.execute(delete(StockDay))
                db.session.execute(delete(StockWeek))
                db.session.execute(delete(Stock))
                db.session.flush()
                print("Tables Deleted!")

                # ---- Stock Master ----
                print(f"Fetching data for Stock Master...")
                stocks = fetch_all_stocks_data()
                for stock in stocks:
                    ticker = stock.ticker
                    if ticker not in stock_master_tickers:
                        stock_master_tickers.add(ticker)
                        new_stock_master.append(stock)
                    else:
                        print(f"Duplicate ticker skipped: {stock.ticker}.")

                print(f"Skipped {len(stocks) - len(new_stock_master)} duplicate tickers.")
                print(f"Total of {len(new_stock_master)} stocks fetched from polygon API!")

                print(f"Flushing Stock Master Table...")
                update_stock_master()

                db.session.flush()

                stock_master_map = {
                    sm.ticker: sm
                    for sm in get_all_stock_master()
                }
                print(f"Flushed Stock Master Table!")

                # ---- Indices and holdings ----
                print(f"Fetching data for indices...")
                with db.session.no_autoflush:
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
                                stock = get_or_fetch_stock(ticker, now_date, stock_master_map)
                                if stock:
                                    index_holding = IndexHolding(
                                        index=index_obj,
                                        stock=stock,
                                        weight=holding.get("weight"),
                                    )
                                    new_index_holdings.append(index_holding)
                        print(f"Fetched data for: {index}!")
                print(f"Fetched data for indices!")

                print("\nFlushing the database with the new fetched data...")
                # Insert new data
                db.session.add_all(new_indices)
                db.session.add_all(new_stocks)
                for value in new_chart_data.values():
                    db.session.add_all(value)
                db.session.add_all(new_index_holdings)

                db.session.flush()
                print("Flushed the database with the new fetched data!\n")


                print("Fetching Top Stocks data for updated database...")

                # Clearing the collected data to collect data for top stocks
                clear_stocks_data()

                with db.session.no_autoflush:
                    for category in get_top_stocks_categories().keys():
                        for stocks_type in ["gainers", "losers", "top_traded"]:
                            for stock in db_get_top_stocks_data(category, stocks_type):
                                ticker = stock.ticker
                                if ticker:
                                    get_or_fetch_stock(ticker, now_date, stock_master_map)

                print("Fetched Top Stocks data for updated database!")

                # Flush Top Stocks and their chart data
                print("Flushing Top Stocks data in the database...")
                add_new_stocks_data()
                print("Flushed Top Stocks data in the database!")


                print("Fetching Trending Stocks data for updated database...")

                # Clearing the collected data to collect data for trending stocks
                clear_stocks_data()

                with db.session.no_autoflush:
                    for item in get_query_stocks(query=None).json:
                        ticker = item.get("ticker")
                        if ticker:
                            get_or_fetch_stock(ticker, now_date, stock_master_map)

                print("Fetched Trending Stocks data for updated database!")

                # Flush Trending Stocks and their chart data
                print("Flushing Trending Stocks data in the database...")
                add_new_stocks_data()
                print("Flushed Trending Stocks data in the database!")

                # -------- Transactional Replace --------
                print("\nCommiting all the data to the database...")
                # Data will be automatically committed to the database by db.session.begin()
                print("Committed all the data to the database...")

            save_populate_db_info(now)

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

        print("\nDatabase Population Completed!\n")

def save_populate_db_info(now):
    # Define file path
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_file = data_dir / "populate_db_info.json"

    # Ensure folder exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Set current timestamp in US/Eastern
    formatted_timestamp = format_dt_et(now)
    # Set current date
    formatted_date = format_date(now)

    # Prepare data
    populate_db_info = {
        "last_updated": formatted_timestamp,
        "last_updated_date": formatted_date
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
