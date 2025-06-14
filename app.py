from flask import Flask, render_template
from models.database import db, Stock, Index, IndexHolding
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

@app.route("/stock")
def all_stocks():
    return render_template("all_stocks.html")

@app.route("/index")
def all_indexes():
    indexes = db.session.execute(db.select(Index)).scalars().all()

    return render_template("all_indexes.html", indexes=indexes)

@app.route("/index/<string:index_id>")
def show_index(index_id):
    index = Index.query.filter_by(slug=index_id).first_or_404()
    index_data = (
        db.session.query(
            IndexHolding.rank,
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.last_close,
            Stock.dma_200,
            Stock.perc_diff
        )
        .join(Stock, IndexHolding.stock_id == Stock.id)
        .join(Index, IndexHolding.index_id == Index.id)
        .filter(Index.id == index.id)
        .order_by(IndexHolding.rank.asc())
        .all()
    )
    return render_template(
        "show_index.html",
        index_name=index.name,
        index_slug=index.slug,
        index_data=index_data,
        get_stock_color=get_stock_color
    )

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
