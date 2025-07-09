# This script generates top stock data for the Overall Market and selected Indexes
# (S&P 500, Nasdaq 100, Dow Jones).
# It returns the top gainers, losers, and most traded stocks for each category.

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import or_

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

from models.database import db, StockMaster, Stock, Index, IndexHolding

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

def get_top_stocks():
    """
    Collects and returns the top gainers, losers, and top traded stocks
    for the overall market and each specified index using ORM queries.

    :return: top_stocks dict.
    """

    top_stocks = {}
    with app.app_context():
        # Query all stocks from StockMaster for overall market data
        all_stocks_data = db.session.query(StockMaster).with_entities(
            StockMaster.ticker,
            StockMaster.name,
            StockMaster.todays_change_perc,
            StockMaster.todays_change,
            StockMaster.volume
        )
        # Top Gainers
        gainers = all_stocks_data.order_by(
            StockMaster.todays_change_perc.desc()
        ).limit(NUM_TOP_STOCKS).all()

        # Top Losers
        losers = all_stocks_data.order_by(
            StockMaster.todays_change_perc.asc()
        ).limit(NUM_TOP_STOCKS).all()

        # Top Stocks traded by Volume
        top_traded = all_stocks_data.order_by(
            StockMaster.volume.desc()
        ).limit(NUM_TOP_STOCKS).all()

        top_stocks = add_to_top_stocks(top_stocks, "overall", "Overall Market", gainers, losers, top_traded)

        # Filter and loop over specific indexes to get their constituent stocks
        # and compute their top movers
        indexes = Index.query.filter(or_(
            Index.slug == "sp500",
            Index.slug == "nasdaq100",
            Index.slug == "dowjones"
        )).all()
        for index in indexes:
            # Query stocks that are part of the current index using IndexHolding join
            index_holdings = db.session.query(
                Stock.ticker,
                Stock.name,
                Stock.todays_change_perc,
                Stock.todays_change,
                Stock.volume
            ).select_from(IndexHolding).join(
                Stock, IndexHolding.stock_id == Stock.id
            ).filter(
                IndexHolding.index_id == index.id
            )

            # Top Gainers
            gainers = index_holdings.order_by(
                Stock.todays_change_perc.desc()
            ).limit(NUM_TOP_STOCKS).all()

            # Top Losers
            losers = index_holdings.order_by(
                Stock.todays_change_perc.asc()
            ).limit(NUM_TOP_STOCKS).all()

            # Top Stocks traded by Volume
            top_traded = index_holdings.order_by(
                Stock.volume.desc()
            ).limit(NUM_TOP_STOCKS).all()

            top_stocks = add_to_top_stocks(top_stocks, index.slug, index.name, gainers, losers, top_traded)

    return top_stocks

def add_to_top_stocks(top_stocks, key, name, gainers, losers, top_traded):
    """
    Helper function to organize the top stock data in a structured dictionary format
    """
    top_stocks[key] = {
        "name": name,
        "attributes": {
            "gainers": gainers,
            "losers": losers,
            "top_traded": top_traded
        }
    }
    return top_stocks
