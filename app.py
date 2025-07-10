"""
RM-Stock-Tracker

A lightweight and professional web app to search U.S. stocks and explore major market
indexes using live financial data — built with Python, Flask, SQLAlchemy, and Bootstrap.

Live Website: https://www.rmstocktracker.com/

Created By: Raghav Mangat
"""

import os
import random
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
from sqlalchemy import and_, or_
from models.database import db, Stock, Index, IndexHolding, StockMaster
from data_collectors.stock_data import fetch_stock_data
from utils.filters import register_custom_filters
from utils.error_handlers import register_error_handlers
from utils.breadcrumbs import generate_breadcrumbs
from utils.top_stocks import get_top_stocks
from utils.populate_db_info import db_last_updated

# Load environment variables
load_dotenv()

# Initialize the Flask App
app = Flask(__name__)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_size': 5,
    'max_overflow': 0
}

# Initialize the database
db.init_app(app)

# Register custom filters
register_custom_filters(app)

# Register error handlers
register_error_handlers(app)

# Make breadcrumbs available to all templates
@app.context_processor
def inject_breadcrumbs():
    return {'breadcrumbs': generate_breadcrumbs()}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/indexes")
def all_indexes():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    indexes = db.session.execute(db.select(Index)).scalars().all()

    return render_template(
        "all_indexes.html",
        indexes=indexes,
        last_updated=last_updated
    )

@app.route("/indexes/<string:index_id>")
def show_index(index_id):
    sort_by = request.args.get('sort_by')
    order = request.args.get('order')
    filter_by = request.args.getlist('filter')

    valid_sort_by = {"weight", "name", "todays_change", "perc_diff"}
    valid_order = {"asc", "desc"}
    valid_filter = {"dark_green", "green", "yellow", "red", "dark_red"}

    # Normalize input
    if sort_by not in valid_sort_by:
        sort_by = None
    if order not in valid_order:
        order = None
    if not filter_by or not set(filter_by).issubset(valid_filter):
        filter_by = list(valid_filter)

    sort_dropdown_options = [
        {"label": "Weight (High to Low)", "sort_by": None, "order": None},
        {"label": "Weight (Low to High)", "sort_by": "weight", "order": "asc"},
        {"label": "Name (High to Low)", "sort_by": "name", "order": "desc"},
        {"label": "Name (Low to High)", "sort_by": "name", "order": "asc"},
        {"label": "Today's Change (High to Low)", "sort_by": "todays_change", "order": "desc"},
        {"label": "Today's Change (Low to High)", "sort_by": "todays_change", "order": "asc"},
        {"label": "200-DMA % Diff (High to Low)", "sort_by": "perc_diff", "order": "desc"},
        {"label": "200-DMA % Diff (Low to High)", "sort_by": "perc_diff", "order": "asc"},
    ]

    sort_options = {
        ("weight", "asc"): IndexHolding.weight.asc(),
        ("name", "desc"): Stock.name.desc(),
        ("name", "asc"): Stock.name.asc(),
        ("todays_change", "desc"): Stock.todays_change_perc.desc(),
        ("todays_change", "asc"): Stock.todays_change_perc.asc(),
        ("perc_diff", "desc"): Stock.dma_200_perc_diff.desc(),
        ("perc_diff", "asc"): Stock.dma_200_perc_diff.asc(),
    }

    # Build filtering conditions
    filter_conditions = []
    for color in filter_by:
        if color == "dark_green":
            filter_conditions.append(Stock.dma_200_perc_diff >= 10)
        elif color == "green":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= 2, Stock.dma_200_perc_diff < 10))
        elif color == "yellow":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= -2, Stock.dma_200_perc_diff < 2))
        elif color == "red":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= -10, Stock.dma_200_perc_diff < -2))
        elif color == "dark_red":
            filter_conditions.append(Stock.dma_200_perc_diff < -10)
    # Colour options and associated dummy values for the filter
    filter_colors = {
        "dark_green": 15,
        "green": 5,
        "yellow": 0,
        "red": -5,
        "dark_red": -15
    }

    # Fetch index
    index = Index.query.filter_by(slug=index_id).first_or_404()

    query = (
        db.session.query(
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.day_close,
            Stock.low_52w,
            Stock.high_52w,
            Stock.todays_change_perc,
            Stock.todays_change,
            Stock.dma_200,
            Stock.dma_200_perc_diff
        )
        .join(Stock, IndexHolding.stock_id == Stock.id)
        .filter(IndexHolding.index_id == index.id)
    )

    # Only include NULLs if all filters are selected
    if set(filter_by) == valid_filter:
        query = query.filter(or_(*filter_conditions, Stock.dma_200_perc_diff.is_(None)))
    else:
        query = query.filter(or_(*filter_conditions))

    index_data = query.order_by(
        sort_options.get((sort_by, order), IndexHolding.weight.desc())
    ).all()

    return render_template(
        "show_index.html",
        index=index,
        index_data=index_data,
        filter_colors=filter_colors,
        sort_dropdown_options=sort_dropdown_options,
        sort_by=sort_by,
        order=order,
    )

@app.route("/stocks")
def all_stocks():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    # Get all stocks in S&P 500 Index in descending order of weight
    sp500_stocks = db.session.query(
        Stock.ticker,
        Stock.volume,
        Stock.day_close,
        Stock.todays_change,
    ).select_from(IndexHolding).join(
        Stock, IndexHolding.stock_id == Stock.id
    ).order_by(IndexHolding.weight.desc()).all()

    # Get all stocks from StockMaster Table
    all_stocks_data = StockMaster.query.all()

    # Get top 10 stocks in sp500
    ticker_tape_stocks = sp500_stocks[:10]
    # Add 20 random stocks from remaining stocks in sp500
    ticker_tape_stocks.extend(random.sample(sp500_stocks[10:], 20))
    # Add 20 random stocks from all stocks in StockMaster Table
    ticker_tape_stocks.extend(random.sample(all_stocks_data, 20))
    # Shuffle the selected 50 ticker tape stocks
    random.shuffle(ticker_tape_stocks)

    # Get the top stocks
    top_stocks = get_top_stocks()

    return render_template(
        "all_stocks.html",
        last_updated=last_updated,
        ticker_tape_stocks=ticker_tape_stocks,
        top_stocks=top_stocks
    )

@app.route("/query_stocks")
def query_stocks():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    query_upper = query.upper()

    # Get matching stocks: prioritize ticker startswith first, then name startswith, then anywhere match
    ticker_startswith = db.session.query(StockMaster).filter(StockMaster.ticker.like(f"{query_upper}%")).limit(5)
    name_startswith = db.session.query(StockMaster).filter(StockMaster.name.ilike(f"{query}%")).limit(5)
    partial_matches = db.session.query(StockMaster).filter(
        StockMaster.ticker.ilike(f"%{query}%") | StockMaster.name.ilike(f"%{query}%")
    ).limit(10)

    # Merge results while preserving order and avoiding duplicates
    seen = set()
    final_results = []

    for q in [ticker_startswith, name_startswith, partial_matches]:
        for stock in q:
            if stock.ticker not in seen:
                final_results.append(stock)
                seen.add(stock.ticker)

    return jsonify([{"ticker": s.ticker, "name": s.name} for s in final_results])

@app.route("/stocks/<string:ticker>")
def show_stock(ticker):
    # To verify if the given ticker is valid
    stock = StockMaster.query.filter_by(ticker=ticker).first()
    if not stock:
        abort(404)
    # Check if the stock is present in the database
    stock = Stock.query.filter_by(ticker=ticker).first()
    # if not in db then use stock data collector script to get stock data
    if not stock:
        stock = fetch_stock_data(ticker)

    # Get the list of related companies
    rel_companies = []
    if stock and stock.related_companies:
        rel_companies = stock.related_companies.split(',')

    return render_template(
        "show_stock.html",
        stock=stock,
        rel_companies=rel_companies,
    )


if __name__ == "__main__":
    app.run()
