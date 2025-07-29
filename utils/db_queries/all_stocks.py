import random
from sqlalchemy import or_
from models.database import db, StockMaster, Stock, Index, IndexHolding

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

def get_ticker_tape_stocks():
    # Get all stocks in S&P 500 Index in descending order of weight
    sp500_stocks = db.session.query(
        Stock.ticker,
        Stock.volume,
        Stock.day_close,
        Stock.todays_change,
    ).select_from(IndexHolding).join(
        Stock, IndexHolding.stock_id == Stock.id
    ).order_by(IndexHolding.weight.desc()).all()

    # Get all stocks from StockMaster Table
    all_stocks_data = StockMaster.query.all()

    # Get top 10 stocks in sp500
    ticker_tape_stocks = sp500_stocks[:10]
    # Add 20 random stocks from remaining stocks in sp500
    ticker_tape_stocks.extend(random.sample(sp500_stocks[10:], 20))
    # Add 20 random stocks from all stocks in StockMaster Table
    ticker_tape_stocks.extend(random.sample(all_stocks_data, 20))
    # Shuffle the selected 50 ticker tape stocks
    random.shuffle(ticker_tape_stocks)

    return ticker_tape_stocks

def get_top_stocks():
    """
    Collects and returns the top gainers, losers, and top traded stocks
    for the overall market and each specified index using ORM queries.

    :return: top_stocks dict.
    """

    # Dict of data to return
    top_stocks = {}

    # Query all stocks from StockMaster for overall market data
    all_stocks_data = db.session.query(StockMaster).with_entities(
        StockMaster.ticker,
        StockMaster.name,
        StockMaster.day_close,
        StockMaster.todays_change_perc,
        StockMaster.todays_change,
        StockMaster.volume
    )
    # Top Gainers
    gainers = all_stocks_data.filter(
        StockMaster.todays_change > 0
    ).order_by(
        StockMaster.todays_change_perc.desc()
    ).limit(NUM_TOP_STOCKS).all()

    # Top Losers
    losers = all_stocks_data.filter(
        StockMaster.todays_change < 0
    ).order_by(
        StockMaster.todays_change_perc.asc()
    ).limit(NUM_TOP_STOCKS).all()

    # Top Stocks traded by Volume
    top_traded = all_stocks_data.order_by(
        StockMaster.volume.desc()
    ).limit(NUM_TOP_STOCKS).all()

    top_stocks = add_to_top_stocks(top_stocks, "overall", "Overall Market", gainers, losers, top_traded)

    # Filter and loop over specific indices to get their constituent stocks
    # and compute their top movers
    indices = Index.query.filter(or_(
        Index.slug == "sp500",
        Index.slug == "nasdaq100",
        Index.slug == "dowjones"
    )).all()
    for index in indices:
        # Query stocks that are part of the current index using IndexHolding join
        index_holdings = db.session.query(
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

        # Top Gainers
        gainers = index_holdings.filter(
            Stock.todays_change > 0
        ).order_by(
            Stock.todays_change_perc.desc()
        ).limit(NUM_TOP_STOCKS).all()

        # Top Losers
        losers = index_holdings.filter(
            Stock.todays_change < 0
        ).order_by(
            Stock.todays_change_perc.asc()
        ).limit(NUM_TOP_STOCKS).all()

        # Top Stocks traded by Volume
        top_traded = index_holdings.order_by(
            Stock.volume.desc()
        ).limit(NUM_TOP_STOCKS).all()

        top_stocks = add_to_top_stocks(top_stocks, index.slug, index.name, gainers, losers, top_traded)
    return top_stocks

def add_to_top_stocks(top_stocks, key, name, gainers, losers, top_traded):
    """
    Helper function to organize the top stock data in a structured dictionary format
    """
    top_stocks[key] = {
        "name": name,
        "attributes": {
            "gainers": gainers,
            "losers": losers,
            "top_traded": top_traded
        }
    }
    return top_stocks