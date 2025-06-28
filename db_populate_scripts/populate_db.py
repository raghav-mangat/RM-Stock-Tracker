import os
import sys
import pytz
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from pathlib import Path

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

from models.database import db, Stock, Index, IndexHolding, StockMaster
from data_collectors.index_data import indexes, fetch_index_data
from data_collectors.stock_data import fetch_stock_data, get_all_stocks, stock_attributes

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

def update_stocks_master_table():
    print("Updating stocks_master table...")
    db.session.query(StockMaster).delete()
    db.session.commit()

    stocks = get_all_stocks()
    for stock in stocks:
        db.session.add(
            StockMaster(
                ticker=stock.ticker,
                name=stock.name,
                type=stock.type,
                primary_exchange=stock.primary_exchange
            )
        )
    db.session.commit()
    print("stocks_master table updated!")

def add_to_indexes_table(index_data, now):
    index = Index.query.filter_by(slug=index_data.get("slug")).first()
    if not index:
        index = Index(
            name=index_data.get("name"),
            slug=index_data.get("slug"),
            url=index_data.get("url"),
            last_updated = now
        )
        db.session.add(index)
        db.session.flush()
    else:
        index.name = index_data.get("name")
        index.url = index_data.get("url")
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
        for attr in stock_attributes:
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
    with app.app_context():
        print("Starting Database Population...\n")
        db.create_all()
        update_stocks_master_table()

        # Set current timestamp in US/Eastern
        eastern = pytz.timezone("US/Eastern")
        now = datetime.now(eastern)

        for index_data in indexes.values():
            index_id = add_to_indexes_table(index_data, now)
            holdings = fetch_index_data(index_data.get("url"))
            for holding in holdings:
                ticker = holding.get("ticker")
                if ticker:
                    if ticker not in tickers_updated:
                        stock_id = add_to_stocks_table(ticker)
                    else:
                        stock_id = Stock.query.filter_by(ticker=ticker).first().id
                    if index_id and stock_id:
                        add_to_index_holdings_table(index_id, stock_id, holding)
            print(f"Updated data for {index_data.get('name')}!")
        db.session.commit()
        print("\nDatabase Population Completed!")

# Load market status
data_path = Path(__file__).resolve().parent.parent / "data" / "market_status.json"

if data_path.exists():
    with open(data_path) as f:
        market_info = json.load(f)
        market_status = market_info.get("market_status")
    if market_status == "closed":
        print(f"Market status was {market_status} — skipping DB population!")
    else:
        print(f"Market status was {market_status} — proceeding with DB population...")
        populate_db()
else:
    print("Market status file missing — cannot determine whether to proceed with DB population!")
