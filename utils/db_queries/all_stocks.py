import random
from sqlalchemy import or_
from models.database import (
    db, StockMaster, Stock, Index, IndexHolding, TickerTapeStockCache,
    TickerMaster, StockDetail
)
from utils.db_queries.tables.dataset_version import get_active_dataset_id

# Number of top stocks to be shown for each category
NUM_TOP_STOCKS = 50

def get_ticker_tape_stocks(dataset_version_id=None):
    rows = db.session.execute(db.select(TickerTapeStockCache.ticker_id)).scalars().all()

    stocks = (
        db.session.query(
            StockMaster.id,
            TickerMaster.symbol.label("ticker"),
            StockMaster.day_close,
            StockMaster.todays_change,
            StockMaster.todays_change_perc,
            StockMaster.volume,
        )
        .select_from(TickerMaster)
        .join(StockMaster, StockMaster.ticker_id == TickerMaster.id)
        .where(
            TickerMaster.is_active == True,
            TickerMaster.id.in_(rows),
            StockMaster.dataset_version_id == dataset_version_id,
        )
        .all()
    )

    # Randomize order
    random.shuffle(stocks)

    return stocks

def get_trending_stocks(dataset_version_id=None):
    if not dataset_version_id:
        dataset_version_id = get_active_dataset_id()

    trending_stocks = (
        db.session.query(
            TickerMaster.id.label("ticker_id"),
            TickerMaster.symbol.label("ticker"),
            StockDetail.name.label("name"),
            StockMaster.day_close,
            StockMaster.todays_change,
            StockMaster.todays_change_perc,
            StockMaster.volume,
            StockMaster.popularity
        )
        .join(TickerMaster, StockMaster.ticker_id == TickerMaster.id)
        .join(StockDetail, TickerMaster.id == StockDetail.ticker_id)
        .filter(
            TickerMaster.is_active == True,
            StockMaster.dataset_version_id == dataset_version_id,
        )
        .order_by(StockMaster.popularity.desc())
        .limit(NUM_TOP_STOCKS)
        .all()
    )

    return trending_stocks

def get_top_stocks_categories(dataset_version_id):
    # Dict of data to return
    top_stocks_categories = dict()

    top_stocks_categories["overall"] =  "Overall Market"

    # Filter and loop over specific indices
    indices = Index.query.filter(
        Index.dataset_version_id == dataset_version_id,
        or_(
            Index.slug == "sp500",
            Index.slug == "nasdaq100",
            Index.slug == "dow-jones"
        )
    ).all()
    for index in indices:
        top_stocks_categories[index.slug] = index.name

    return top_stocks_categories

def db_get_top_stocks_data(category, stocks_type, dataset_version_id=None):
    stocks = None
    if not dataset_version_id:
        dataset_version_id = get_active_dataset_id()

    if category == "overall":
        # Query all stocks from StockMaster for overall market data
        stocks = (
            db.session.query(
                TickerMaster.symbol.label("ticker"),
                StockDetail.name.label("name"),
                StockMaster.day_close,
                StockMaster.todays_change,
                StockMaster.todays_change_perc,
                StockMaster.volume,
            )
            .join(TickerMaster, StockMaster.ticker_id == TickerMaster.id)
            .join(StockDetail, TickerMaster.id == StockDetail.ticker_id)
            .filter(
                TickerMaster.is_active == True,
                StockMaster.dataset_version_id == dataset_version_id,
            )
        )

    elif category in get_top_stocks_categories(dataset_version_id).keys():
        index = Index.query.filter_by(
            dataset_version_id=dataset_version_id,
            slug=category
        ).first()

        # Query stocks that are part of the current index using IndexHolding join
        stocks = (
            db.session.query(
                TickerMaster.symbol.label("ticker"),
                StockDetail.name.label("name"),
                StockMaster.day_close,
                StockMaster.todays_change,
                StockMaster.todays_change_perc,
                StockMaster.volume,
            ).select_from(
                IndexHolding
            ).join(
                Stock, IndexHolding.stock_id == Stock.id
            ).join(
                StockMaster, Stock.stock_master_id == StockMaster.id
            )
            .join(TickerMaster, StockMaster.ticker_id == TickerMaster.id)
            .join(StockDetail, TickerMaster.id == StockDetail.ticker_id)
            .filter(
                TickerMaster.is_active == True,
                IndexHolding.index_id == index.id,
                StockMaster.dataset_version_id == dataset_version_id,
            )
        )

    result = None
    if not stocks:
        return result
    if stocks_type == "gainers":
        # Top Gainers
        result = stocks.filter(
            StockMaster.todays_change_perc > 0
        ).order_by(
            StockMaster.todays_change_perc.desc()
        ).limit(NUM_TOP_STOCKS).all()
    elif stocks_type == "losers":
        # Top Losers
        result = stocks.filter(
            StockMaster.todays_change_perc < 0
        ).order_by(
            StockMaster.todays_change_perc.asc()
        ).limit(NUM_TOP_STOCKS).all()
    elif stocks_type == "top_traded":
        # Top Stocks traded by Volume
        result = stocks.order_by(
            StockMaster.volume.desc()
        ).limit(NUM_TOP_STOCKS).all()

    return result