import os
import sys
from dotenv import load_dotenv
from flask import Flask

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
from data_collectors.stock_data import fetch_stock_data, get_all_stocks

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

def add_to_indexes_table(index_data):
    index = Index.query.filter_by(slug=index_data.get("slug")).first()
    if not index:
        index = Index(
            name=index_data.get("name"),
            slug=index_data.get("slug"),
            url=index_data.get("url"),
        )
        db.session.add(index)
        db.session.flush()
    else:
        index.name = index_data.get("name")
        index.url = index_data.get("url")
    return index.id

def add_to_stocks_table(ticker):
    stock_data = fetch_stock_data(ticker)
    if not stock_data:
        return None

    stock = Stock.query.filter_by(ticker=stock_data.get("ticker")).first()
    if not stock:
        stock = Stock(
            ticker=stock_data.get("ticker"),
            name=stock_data.get("name"),
            description=stock_data.get("description"),
            homepage_url=stock_data.get("homepage_url"),
            list_date=stock_data.get("list_date"),
            industry=stock_data.get("industry"),
            type=stock_data.get("type"),
            total_employees=stock_data.get("total_employees"),
            market_cap=stock_data.get("market_cap"),
            icon_url=stock_data.get("icon_url"),
            last_close=stock_data.get("last_close"),
            last_open=stock_data.get("last_open"),
            day_high=stock_data.get("day_high"),
            day_low=stock_data.get("day_low"),
            volume=stock_data.get("volume"),
            todays_change=stock_data.get("todays_change"),
            todays_change_perc=stock_data.get("todays_change_perc"),
            dma_50=stock_data.get("dma_50"),
            dma_200=stock_data.get("dma_200"),
            dma_200_perc_diff=stock_data.get("dma_200_perc_diff"),
            high_52w=stock_data.get("high_52w"),
            low_52w=stock_data.get("low_52w"),
            related_companies=stock_data.get("related_companies")
        )
        db.session.add(stock)
        db.session.flush()
    else:
        # Update existing fields
        stock.name = stock_data.get("name")
        stock.description = stock_data.get("description")
        stock.homepage_url = stock_data.get("homepage_url")
        stock.list_date = stock_data.get("list_date")
        stock.industry = stock_data.get("industry")
        stock.type = stock_data.get("type")
        stock.total_employees = stock_data.get("total_employees")
        stock.market_cap = stock_data.get("market_cap")
        stock.icon_url = stock_data.get("icon_url")
        stock.last_close = stock_data.get("last_close")
        stock.last_open = stock_data.get("last_open")
        stock.day_high = stock_data.get("day_high")
        stock.day_low = stock_data.get("day_low")
        stock.volume = stock_data.get("volume")
        stock.todays_change = stock_data.get("todays_change")
        stock.todays_change_perc = stock_data.get("todays_change_perc")
        stock.dma_50 = stock_data.get("dma_50")
        stock.dma_200 = stock_data.get("dma_200")
        stock.dma_200_perc_diff = stock_data.get("dma_200_perc_diff")
        stock.high_52w = stock_data.get("high_52w")
        stock.low_52w = stock_data.get("low_52w")
        stock.related_companies = stock_data.get("related_companies")
    return stock.id

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
        index_holding.rank = holding.get("rank")

with app.app_context():
    print("Starting Database Population...\n")
    db.create_all()
    update_stocks_master_table()

    for index_data in indexes.values():
        index_id = add_to_indexes_table(index_data)
        holdings = fetch_index_data(index_data.get("url"))
        for holding in holdings:
            ticker = holding.get("ticker")
            if not ticker:
                continue
            stock_id = add_to_stocks_table(ticker)
            if stock_id:
                add_to_index_holdings_table(index_id, stock_id, holding)

    db.session.commit()
    print("\nDatabase Population Completed!")
