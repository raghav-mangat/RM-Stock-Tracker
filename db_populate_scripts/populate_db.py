from flask import Flask
from models.database import db, Stock, Index, IndexHolding
from dotenv import load_dotenv
import os
from data_collectors.index_data import indexes, fetch_index_data
from data_collectors.stock_data import fetch_stock_data

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

def add_to_indexes_table():
    index = Index.query.filter_by(slug=index_data.get("slug")).first()
    if not index:
        index = Index(
            name=index_data.get("name"),
            slug=index_data.get("slug"),
            url=index_data.get("url"),
        )
        db.session.add(index)
        db.session.commit()
    else:
        index.name = index_data.get("name")
        index.url = index_data.get("url")
        db.session.commit()
    return index.id

def add_to_stocks_table():
    stock_data = fetch_stock_data(ticker)
    stock = Stock.query.filter_by(ticker=stock_data.get("ticker", "N/A")).first()
    if not stock:
        stock = Stock(
            ticker=stock_data.get("ticker", "N/A"),
            name=stock_data.get("name", "N/A"),
            last_close=stock_data.get("last_close", 0),
            dma_200=stock_data.get("dma_200", 0),
            perc_diff=stock_data.get("perc_diff", 0)
        )
        db.session.add(stock)
        db.session.commit()
    else:
        stock.name = stock_data.get("name", "N/A")
        stock.last_close = stock_data.get("last_close", 0)
        stock.dma_200 = stock_data.get("dma_200", 0)
        stock.perc_diff = stock_data.get("perc_diff", 0)
        db.session.commit()
    return stock.id

def add_to_index_holdings_table():
    index_holding = IndexHolding.query.filter_by(index_id=index_id, stock_id=stock_id).first()
    if not index_holding:
        index_holding = IndexHolding(
            index_id=index_id,
            stock_id=stock_id,
            rank=holding.get("rank"),
            weight=holding.get("weight"),
        )
        db.session.add(index_holding)
        db.session.commit()
    else:
        index_holding.rank = holding.get("rank")
        index_holding.weight = holding.get("weight")
        db.session.commit()

with app.app_context():
    db.create_all()
    for index_data in indexes.values():
        index_id = add_to_indexes_table()
        holdings = fetch_index_data(index_data.get("url"))
        for holding in holdings:
            ticker = holding.get("ticker", "N/A")
            stock_id = add_to_stocks_table()
            add_to_index_holdings_table()
    print("\nDatabase Population Completed!")
