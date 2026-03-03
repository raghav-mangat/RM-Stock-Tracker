from datetime import datetime
from models.database import db, StockMaster, Stock
from flask import abort
from sqlalchemy.orm import joinedload
from data_collectors.stock_data import fetch_stock_data, fetch_chart_data, TIMEFRAME_OPTIONS, SELECT_DB_TABLE, \
    DB_TIMEFRAMES
from utils.datetime_utils import DATE_FORMAT, convert_to_et_dt, format_dt_et

def get_stock_data(stock_master=None, now=None):
    # Check if the stock is present in the database
    stock = (
        db.session.query(Stock)
        .options(
            joinedload(Stock.stock_master),
        )
        .filter(Stock.stock_master_id == stock_master.id)
        .first()
    )

    # If not in db then use stock data collector script to get stock data
    if not stock:
        stock = fetch_stock_data(stock_master=stock_master, now=now)
        db.session.add(stock)
        db.session.flush()

    # Get the list of related companies
    rel_companies = []
    if stock and stock.related_companies:
        rel_companies = stock.related_companies.split(',')

    # Get the stock type
    stock_type = stock.stock_master.stock_type.description if stock and stock.stock_master else None

    # Get the last updated time
    last_updated = None
    if stock and stock.stock_master:
        last_updated = format_dt_et(stock.stock_master.last_updated)

    result = {
        "stock": stock.to_dict() if stock else None,
        "stock_type": stock_type,
        "rel_companies": rel_companies,
        "last_updated": last_updated
    }
    return result

def get_chart_data(timeframe, stock_master=None, now=None):
    # Check if the stock is present in the database
    stock = (
        db.session.query(Stock)
        .options(
            joinedload(Stock.stock_master),
        )
        .filter(Stock.stock_master_id == stock_master.id)
        .first()
    )

    timeframe_data = TIMEFRAME_OPTIONS[timeframe]

    if stock:
        stock_id = stock.id
        db_table = SELECT_DB_TABLE.get(timeframe_data["timespan"])
        query = db_table.query.filter_by(stock_id=stock_id)
        if timeframe not in DB_TIMEFRAMES:
            before = timeframe_data.get("before")(datetime.strptime(now, DATE_FORMAT))
            query = query.filter(db_table.date >= before)
        chart_data = query.order_by(db_table.date.asc()).all()

        # Fallback if no chart data exists
        if not chart_data:
            chart_data = fetch_chart_data(stock, timeframe, now)

    else:
        stock = Stock(stock_master=stock_master)
        chart_data = fetch_chart_data(stock, timeframe, now)

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

    change_perc = None
    if len(close_price_data) > 1:
        start = close_price_data[0]
        end = close_price_data[-1]

        if start not in (None, 0) and end is not None:
            change_perc = round(((end - start) * 100 / start), 2)

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
    stock_master = StockMaster.query.filter_by(ticker=ticker).first()

    if not stock_master:
        abort(404)

    return stock_master

def get_timeframe_options():
    return list(TIMEFRAME_OPTIONS.keys())