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

import pytz
import json
from datetime import datetime
from flask import Flask
from pathlib import Path
from models.database import db, Stock, Index, IndexHolding, StockMaster
from data_collectors.index_data import all_indexes, get_index_info, fetch_index_data
from data_collectors.stock_data import STOCK_ATTRIBUTES, fetch_all_stocks_data, fetch_stock_data
from utils.datetime_utils import format_et_datetime
from utils.top_stocks import get_top_stocks

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

def update_stocks_master_table():
    print("Updating stocks_master table...")
    db.session.query(StockMaster).delete()
    db.session.commit()

    # Get a list of all stocks data from Polygon API
    stocks = fetch_all_stocks_data()
    # To avoid adding duplicate data
    tickers_added = set()
    # To count the number of duplicates
    duplicates = []

    for stock in stocks:
        ticker_upper = stock.ticker.upper()
        # Only add to DB if it's unique
        if ticker_upper not in tickers_added:
            tickers_added.add(ticker_upper)
            db.session.add(stock)
            db.session.flush()
        else:
            duplicates.append(stock.ticker)
            print(f"Duplicate ticker skipped: {stock.ticker}")
    print(f"Skipped {len(duplicates)} duplicate tickers.")

    db.session.commit()
    print("Updated stocks_master table!")

def add_to_indexes_table(index, now):
    index_info = get_index_info(index)
    index = Index.query.filter_by(slug=index_info.get("slug")).first()
    if not index:
        index = Index(
            name=index_info.get("name"),
            slug=index_info.get("slug"),
            url=index_info.get("url"),
            last_updated = now
        )
        db.session.add(index)
        db.session.flush()
    else:
        index.name = index_info.get("name")
        index.url = index_info.get("url")
        index.last_updated = now
    return index.id

def add_to_stocks_table(ticker):
    stock_data = fetch_stock_data(ticker)
    if not stock_data:
        return None

    tickers_updated.add(stock_data.ticker)
    # Check if a stock with the same ticker already exists
    existing_stock = Stock.query.filter_by(ticker=stock_data.ticker).first()
    if not existing_stock:
        db.session.add(stock_data)
        db.session.flush()
    else:
        # Update the existing stock with values from stock_data
        for attr in STOCK_ATTRIBUTES:
            setattr(existing_stock, attr, getattr(stock_data, attr))
        db.session.flush()
    return stock_data.id

def add_to_index_holdings_table(index_id, stock_id, holding):
    index_holding = IndexHolding.query.filter_by(index_id=index_id, stock_id=stock_id).first()
    if not index_holding:
        index_holding = IndexHolding(
            index_id=index_id,
            stock_id=stock_id,
            weight=holding.get("weight"),
        )
        db.session.add(index_holding)
        db.session.flush()
    else:
        index_holding.weight = holding.get("weight")

# To keep track of tickers already updated in the database
tickers_updated = set()
def populate_db():
    """
    Populates the Database using the data and functions defined
    in index and stock data_collectors scripts.
    :return: None
    """
    with app.app_context():
        print("Starting Database Population...\n")
        db.create_all()
        update_stocks_master_table()

        # Set current timestamp in US/Eastern
        eastern = pytz.timezone("US/Eastern")
        now = datetime.now(eastern)

        # Save the data for all indexes and the constituent stocks
        for index in all_indexes:
            index_id = add_to_indexes_table(index, now)
            holdings = fetch_index_data(index)
            for holding in holdings:
                ticker = holding.get("ticker")
                if ticker:
                    if ticker not in tickers_updated:
                        stock_id = add_to_stocks_table(ticker)
                    else:
                        stock_id = Stock.query.filter_by(ticker=ticker).first().id
                    if index_id and stock_id:
                        add_to_index_holdings_table(index_id, stock_id, holding)
            print(f"Updated data for: {index}!")
        db.session.commit()

        print(f"Storing data for top stocks...")
        # Get the top stocks from StockMaster table for each category
        top_stocks = get_top_stocks()
        # Save the stocks data in the Stocks table
        for category in top_stocks.values():
            for attribute_stocks in category.get("attributes").values():
                for stock in attribute_stocks:
                    ticker = stock.ticker
                    if ticker not in tickers_updated:
                        add_to_stocks_table(ticker)
        db.session.commit()
        print(f"Stored data for top stocks!")

        save_populate_db_info()
        print("\nDatabase Population Completed!")

def save_populate_db_info():
    # Define file path
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_file = data_dir / "populate_db_info.json"

    # Ensure folder exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Set current timestamp in US/Eastern
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    timestamp = format_et_datetime(now)

    # Prepare data
    populate_db_info = {
        "last_updated": timestamp,
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