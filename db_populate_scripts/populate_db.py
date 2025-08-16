import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

IS_RELEASE = os.getenv("IS_RELEASE")

if IS_RELEASE == "1":
    # Ensure the project root is in Python's path: in PythonAnywhere
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
elif IS_RELEASE == "0":
    # Ensure the instance folder exists for the database: in local PC
    db_uri = os.getenv("DATABASE_URI")
    if db_uri and db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

import json
from flask import Flask
from pathlib import Path
from sqlalchemy import delete
from models.database import db, Stock, Index, IndexHolding, StockMaster, StockMinute, StockHour, StockDay, StockWeek
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import fetch_all_stocks_data, fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES
from utils.datetime_utils import get_current_et, format_et_datetime, format_date
from utils.db_queries.all_stocks import get_top_stocks

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

# -------- Stage all new data --------
stocks_cache = {}  # ticker -> Stock object
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

        db.create_all()

        # ---- Stock Master ----
        stocks = fetch_all_stocks_data()
        seen_tickers = set()
        for stock in stocks:
            ticker_upper = stock.ticker.upper()
            if ticker_upper not in seen_tickers:
                seen_tickers.add(ticker_upper)
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
                db.session.execute(delete(StockMaster))

                # Insert new data
                db.session.add_all(new_stock_master)
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
        top_stocks = get_top_stocks()

        # Clearing the collected data to collect data for top stocks
        new_stocks.clear()
        for data_list in new_chart_data.values():
            data_list.clear()

        for top_stocks_category in top_stocks.values():
            for category_stocks in top_stocks_category.get("category").values():
                for stock in category_stocks:
                    ticker = stock.ticker
                    if ticker:
                        get_or_fetch_stock(ticker, now_date)

        # Insert Top Stocks and their chart data
        if new_stocks or any(new_chart_data.values()):
            db.session.add_all(new_stocks)
            for value in new_chart_data.values():
                db.session.add_all(value)
            db.session.commit()
        print("Top Stocks data stored in the database!")

        db.session.close()
        print("\nDatabase Population Completed!")

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
    else:
        print("Market status file missing - cannot determine whether to proceed with DB population!")

if __name__ == "__main__":
    main()
