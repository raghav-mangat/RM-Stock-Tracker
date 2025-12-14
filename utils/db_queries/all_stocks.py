import random
from sqlalchemy import or_
from models.database import db, StockMaster, Stock, Index, IndexHolding

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

def get_ticker_tape_stocks():
    # Get all stocks in Nasdaq 100 Index in descending order of weight
    nasdaq100_stocks = (db.session.query(
        Stock.ticker,
        Stock.volume,
        Stock.day_close,
        Stock.todays_change,
    ).select_from(IndexHolding).join(
        Stock, IndexHolding.stock_id == Stock.id
    ).join(
        Index, IndexHolding.index_id == Index.id
    ).filter(
        Index.slug == "nasdaq100"
    ).order_by(IndexHolding.weight.desc()).all())

    # Get all stocks from StockMaster Table
    all_stocks_data = (db.session.query(
        StockMaster.ticker,
        StockMaster.volume,
        StockMaster.day_close,
        StockMaster.todays_change,
    ).all())

    # Get top 10 stocks in nasdaq100
    ticker_tape_stocks = nasdaq100_stocks[:10]
    # Add 20 random stocks from remaining stocks in nasdaq100
    ticker_tape_stocks.extend(random.sample(nasdaq100_stocks[10:], 20))
    # Add 20 random stocks from all stocks in StockMaster Table
    ticker_tape_stocks.extend(random.sample(all_stocks_data, 20))
    # Shuffle the selected 50 ticker tape stocks
    random.shuffle(ticker_tape_stocks)

    return ticker_tape_stocks

def get_top_stocks_categories():
    # Dict of data to return
    top_stocks_categories = dict()

    top_stocks_categories["overall"] =  "Overall Market"

    # Filter and loop over specific indices
    indices = Index.query.filter(or_(
        Index.slug == "sp500",
        Index.slug == "nasdaq100",
        Index.slug == "dowjones"
    )).all()
    for index in indices:
        top_stocks_categories[index.slug] = index.name

    return top_stocks_categories

def db_get_top_stocks_data(category, stocks_type):
    stocks = None
    table = None
    if category == "overall":
        # Query all stocks from StockMaster for overall market data
        stocks = db.session.query(StockMaster).with_entities(
            StockMaster.ticker,
            StockMaster.name,
            StockMaster.day_close,
            StockMaster.todays_change_perc,
            StockMaster.todays_change,
            StockMaster.volume
        )
        table = StockMaster

    elif category in get_top_stocks_categories().keys():
        index = Index.query.filter(
            Index.slug == category,
        ).first()
        # Query stocks that are part of the current index using IndexHolding join
        stocks = db.session.query(
            Stock.ticker,
            Stock.name,
            Stock.day_close,
            Stock.todays_change_perc,
            Stock.todays_change,
            Stock.volume
        ).select_from(IndexHolding).join(
            Stock, IndexHolding.stock_id == Stock.id
        ).filter(
            IndexHolding.index_id == index.id
        )
        table = Stock

    result = None
    if stocks is None or table is None:
        return result
    if stocks_type == "gainers":
        # Top Gainers
        result = stocks.filter(
            table.todays_change_perc > 0
        ).order_by(
            table.todays_change_perc.desc()
        ).limit(NUM_TOP_STOCKS).all()
    elif stocks_type == "losers":
        # Top Losers
        result = stocks.filter(
            table.todays_change_perc < 0
        ).order_by(
            table.todays_change_perc.asc()
        ).limit(NUM_TOP_STOCKS).all()
    elif stocks_type == "top_traded":
        # Top Stocks traded by Volume
        result = stocks.order_by(
            table.volume.desc()
        ).limit(NUM_TOP_STOCKS).all()

    return result