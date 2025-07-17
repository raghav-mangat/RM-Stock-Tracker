# This script generates top stock data for the Overall Market and selected Indices
# (S&P 500, Nasdaq 100, Dow Jones).
# It returns the top gainers, losers, and most traded stocks for each category.

from sqlalchemy import or_
from models.database import db, StockMaster, Stock, Index, IndexHolding

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

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
