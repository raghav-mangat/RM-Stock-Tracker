from models.database import StockMaster, Stock
from flask import abort
from data_collectors.stock_data import fetch_stock_data

def get_stock_data(ticker):
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

    result = {
        "stock": stock,
        "rel_companies": rel_companies
    }
    return result