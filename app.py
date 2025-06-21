from flask import Flask, render_template, request, jsonify, abort
from models.database import db, Stock, Index, IndexHolding, StockMaster
from dotenv import load_dotenv
from data_collectors.stock_data import fetch_stock_data
import os

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

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

    valid_sort_by = {"weight", "last_close", "dma_200", "perc_diff"}
    valid_order = {"asc", "desc"}

    if (sort_by not in valid_sort_by) or (order not in valid_order):
        sort_by = None
        order = None

    dropdown_options = [
        {"label": "Weight (High to Low)", "sort_by": None, "order": None},
        {"label": "Weight (Low to High)", "sort_by": "weight", "order": "asc"},
        {"label": "Last Close (High to Low)", "sort_by": "last_close", "order": "desc"},
        {"label": "Last Close (Low to High)", "sort_by": "last_close", "order": "asc"},
        {"label": "200-DMA (High to Low)", "sort_by": "dma_200", "order": "desc"},
        {"label": "200-DMA (Low to High)", "sort_by": "dma_200", "order": "asc"},
        {"label": "% Diff (High to Low)", "sort_by": "perc_diff", "order": "desc"},
        {"label": "% Diff (Low to High)", "sort_by": "perc_diff", "order": "asc"},
    ]

    sort_options = {
        ("weight", "asc"): IndexHolding.weight.asc(),
        ("last_close", "desc"): Stock.last_close.desc(),
        ("last_close", "asc"): Stock.last_close.asc(),
        ("dma_200", "desc"): Stock.dma_200.desc(),
        ("dma_200", "asc"): Stock.dma_200.asc(),
        ("perc_diff", "desc"): Stock.dma_200_perc_diff.desc(),
        ("perc_diff", "asc"): Stock.dma_200_perc_diff.asc(),
    }

    index = Index.query.filter_by(slug=index_id).first_or_404()
    index_data = (
        db.session.query(
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.last_close,
            Stock.dma_200,
            Stock.dma_200_perc_diff
        )
        .join(Stock, IndexHolding.stock_id == Stock.id)
        .filter(IndexHolding.index_id == index.id)
        .order_by(sort_options.get((sort_by, order), IndexHolding.weight.desc()))
        .all()
    )
    return render_template(
        "show_index.html",
        index=index,
        index_data=index_data,
        dropdown_options=dropdown_options,
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

@app.template_filter('stock_color')
def get_stock_color(perc_diff):
    """
    Function to determine stock color based on the percentage
    difference between last closing price and 200 DMA.
    :param perc_diff:
    :return: colour.
    """
    if perc_diff >= 10: # More than 10% above
        return "#66ff66" # Dark Green
    elif perc_diff <= -10: # More than 10% below
        return "#FF6666" # Dark Red
    elif perc_diff >= 2: # Between 2% and 10% above
        return "#99ff99" # Green
    elif perc_diff <= -2:  # Between 2% and 10% below
        return "#FF9999" # Red
    else: # Within ±2%
        return "#ffff66" # Yellow

@app.template_filter('format_et_datetime')
def format_et_datetime(et_datetime):
    return et_datetime.strftime('%A, %b %d, %Y, at %I:%M%p, ET.')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run()
