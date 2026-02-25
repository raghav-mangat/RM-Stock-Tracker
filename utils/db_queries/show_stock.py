from datetime import datetime
from models.database import db, StockMaster, Stock
from flask import abort
from data_collectors.stock_data import fetch_stock_data, fetch_chart_data, TIMEFRAME_OPTIONS, SELECT_DB_TABLE, \
    DB_TIMEFRAMES
from utils.datetime_utils import DATE_FORMAT, convert_to_et_dt
from utils.db_queries.stock_type_meta_data import get_stock_type_by_id
from utils.populate_db_info import db_last_updated_date

def get_stock_data(ticker):
    verify_ticker(ticker)

    # Check if the stock is present in the database
    stock = Stock.query.filter_by(ticker=ticker).first()

    # if not in db then use stock data collector script to get stock data
    if not stock:
        stock = fetch_stock_data(ticker)
        db.session.add(stock)
        db.session.flush()

    # Get the list of related companies
    rel_companies = []
    if stock and stock.related_companies:
        rel_companies = stock.related_companies.split(',')

    # Get the stock type
    stock_type = None
    if stock:
        if stock.stock_type:
            stock_type = stock.stock_type.description
        elif stock.stock_type_id:
            stock_type = get_stock_type_by_id(stock.stock_type_id)
            stock_type = stock_type.description if stock_type else None

    result = {
        "stock": stock.to_dict() if stock else None,
        "stock_type": stock_type,
        "rel_companies": rel_companies
    }
    return result

def get_chart_data(ticker, timeframe):
    verify_ticker(ticker)
    timeframe_data = TIMEFRAME_OPTIONS[timeframe]
    now = db_last_updated_date()

    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock:
        stock_id = stock.id
        db_table = SELECT_DB_TABLE.get(timeframe_data["timespan"])
        query = db_table.query.filter_by(stock_id=stock_id)
        if timeframe not in DB_TIMEFRAMES:
            before = timeframe_data.get("before")(datetime.strptime(now, DATE_FORMAT))
            query = query.filter(db_table.date >= before)
        chart_data = query.order_by(db_table.date.asc()).all()
    else:
        stock = Stock(ticker=ticker)
        chart_data = fetch_chart_data(stock, timeframe)

    ema_data = timeframe_data.get("ema_data")
    date_format = timeframe_data["date_format"]
    date_data = []
    close_price_data = []
    ema_30_data = []
    ema_50_data = []
    ema_200_data = []
    volume_data = []
    for data in chart_data:
        date = convert_to_et_dt(data.date)
        date_data.append(date.strftime(date_format))
        close_price_data.append(float(data.close_price))
        volume_data.append(data.volume)
        if ema_data:
            ema_30_data.append(float(data.ema_30))
            ema_50_data.append(float(data.ema_50))
            ema_200_data.append(float(data.ema_200))

    change_perc = 0
    if len(close_price_data) > 1:
        try:
            change_perc = float(round(((close_price_data[-1] - close_price_data[0]) * 100 / close_price_data[0]), 2))
        except ZeroDivisionError:
            change_perc = 0

    result = {
        "date_data": date_data,
        "close_price_data": close_price_data,
        "volume_data": volume_data,
        "ema_30_data": ema_30_data,
        "ema_50_data": ema_50_data,
        "ema_200_data": ema_200_data,
        "change_perc": change_perc,
        "ema_data": ema_data,
    }
    return result

def verify_ticker(ticker):
    # To verify if the given ticker is valid
    stock = StockMaster.query.filter_by(ticker=ticker).first()
    if not stock:
        abort(404)

def get_timeframe_options():
    return list(TIMEFRAME_OPTIONS.keys())