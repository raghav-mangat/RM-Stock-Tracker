from flask import Flask, render_template, request, jsonify
from models.database import db, Stock, Index, IndexHolding, StockMaster
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

with app.app_context():
    db.create_all()

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
        ("perc_diff", "desc"): Stock.perc_diff.desc(),
        ("perc_diff", "asc"): Stock.perc_diff.asc(),
    }

    index = Index.query.filter_by(slug=index_id).first_or_404()
    index_data = (
        db.session.query(
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.last_close,
            Stock.dma_200,
            Stock.perc_diff
        )
        .join(Stock, IndexHolding.stock_id == Stock.id)
        .filter(IndexHolding.index_id == index.id)
        .order_by(sort_options.get((sort_by, order), IndexHolding.weight.desc()))
        .all()
    )
    return render_template(
        "show_index.html",
        index_name=index.name,
        index_slug=index.slug,
        index_data=index_data,
        dropdown_options=dropdown_options,
        sort_by=sort_by,
        order=order,
        get_stock_color=get_stock_color
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
    return ticker

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

if __name__ == "__main__":
    app.run(debug=True)
