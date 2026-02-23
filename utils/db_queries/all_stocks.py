import random
from sqlalchemy import func, or_
from models.database import db, StockMaster, Stock, Index, IndexHolding, TickerTapeStockCache

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

def get_ticker_tape_stocks():
    rows = TickerTapeStockCache.query.all()

    stocks = [row.stock_master for row in rows if row.stock_master]

    # Randomize order
    random.shuffle(stocks)

    return stocks

def get_trending_stocks():
    popularity = get_stocks_popularity()
    trending_stocks = db.session.query(
        StockMaster.id,
        StockMaster.ticker,
        StockMaster.name,
        StockMaster.day_close,
        StockMaster.todays_change,
        StockMaster.todays_change_perc,
        StockMaster.volume,
        popularity
    ).filter(
        StockMaster.name.isnot(None),
        StockMaster.day_close.isnot(None),
        StockMaster.todays_change.isnot(None),
        StockMaster.todays_change_perc.isnot(None),
        StockMaster.volume.isnot(None),
    ).order_by(
        popularity.desc()
    ).limit(NUM_TOP_STOCKS).all()

    return trending_stocks

def get_stocks_popularity():
    # Estimate popularity using (day close price) * volume
    # Also, called trade activity
    popularity = (
        func.coalesce(StockMaster.day_close, 0) *
        func.coalesce(StockMaster.volume, 0)
    ).label('popularity')

    return popularity

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
            StockMaster.todays_change,
            StockMaster.todays_change_perc,
            StockMaster.volume
        ).filter(
            StockMaster.name.isnot(None),
            StockMaster.day_close.isnot(None),
            StockMaster.todays_change.isnot(None),
            StockMaster.todays_change_perc.isnot(None),
            StockMaster.volume.isnot(None),
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
            Stock.todays_change,
            Stock.todays_change_perc,
            Stock.volume
        ).select_from(IndexHolding).join(
            Stock, IndexHolding.stock_id == Stock.id
        ).filter(
            IndexHolding.index_id == index.id,
            Stock.name.isnot(None),
            Stock.day_close.isnot(None),
            Stock.todays_change.isnot(None),
            Stock.todays_change_perc.isnot(None),
            Stock.volume.isnot(None),
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