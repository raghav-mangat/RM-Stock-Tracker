import os
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
from sqlalchemy import and_, or_, nulls_last
from models.database import db, Stock, Index, IndexHolding, StockMaster
from data_collectors.stock_data import fetch_stock_data
from utils.filters import register_custom_filters
from utils.error_handlers import register_error_handlers
from utils.breadcrumbs import generate_breadcrumbs

# Load environment variables
load_dotenv()

# Initialize the Flask App
app = Flask(__name__)

# Initialize the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
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

@app.route("/all_indexes")
def all_indexes():
    indexes = db.session.execute(db.select(Index)).scalars().all()

    return render_template("all_indexes.html", indexes=indexes)

@app.route("/index/<string:index_id>")
def show_index(index_id):
    sort_by = request.args.get('sort_by')
    order = request.args.get('order')
    filter_by = request.args.getlist('filter')

    valid_sort_by = {"weight", "name", "day_close", "dma_200", "perc_diff"}
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
        {"label": "Day Close (High to Low)", "sort_by": "day_close", "order": "desc"},
        {"label": "Day Close (Low to High)", "sort_by": "day_close", "order": "asc"},
        {"label": "200-DMA (High to Low)", "sort_by": "dma_200", "order": "desc"},
        {"label": "200-DMA (Low to High)", "sort_by": "dma_200", "order": "asc"},
        {"label": "% Diff (High to Low)", "sort_by": "perc_diff", "order": "desc"},
        {"label": "% Diff (Low to High)", "sort_by": "perc_diff", "order": "asc"},
    ]

    sort_options = {
        ("weight", "asc"): IndexHolding.weight.asc(),
        ("name", "desc"): Stock.name.desc(),
        ("name", "asc"): Stock.name.asc(),
        ("day_close", "desc"): Stock.day_close.desc(),
        ("day_close", "asc"): Stock.day_close.asc(),
        ("dma_200", "desc"): Stock.dma_200.desc(),
        ("dma_200", "asc"): Stock.dma_200.asc(),
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

    # Fetch index
    index = Index.query.filter_by(slug=index_id).first_or_404()

    query = (
        db.session.query(
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.day_close,
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
        nulls_last(sort_options.get((sort_by, order), IndexHolding.weight.desc()))
    ).all()

    return render_template(
        "show_index.html",
        index=index,
        index_data=index_data,
        sort_dropdown_options=sort_dropdown_options,
        sort_by=sort_by,
        order=order,
    )

@app.route("/search_stocks")
def search_stocks():
    return render_template("search_stocks.html")

@app.route("/query_stocks")
def query_stocks():
    query = request.args.get("q", "").upper()
    results = (
        db.session.query(StockMaster)
        .filter(StockMaster.ticker.like(f"%{query}%") | StockMaster.name.ilike(f"%{query}%"))
        .limit(10)
        .all()
    )
    return jsonify([{"ticker": s.ticker, "name": s.name} for s in results])

@app.route("/stock/<string:ticker>")
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
