import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from models.database import db, StockTypeMeta, Stock, Index, IndexHolding, StockMaster, StockMinute, StockHour, StockDay, StockWeek
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import fetch_stock_types, fetch_all_stocks_data, fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES
from utils.datetime_utils import get_current_utc, format_dt_et, format_date
from utils.db_queries.stock_master_data import get_all_stock_master
from utils.db_queries.stock_type_meta_data import get_all_stock_types
from utils.db_queries.all_stocks import get_trending_stocks, get_top_stocks_categories, db_get_top_stocks_data
from utils.db_queries.query_stocks import get_query_stocks
from scheduled_scripts.helpers import write_to_status_file, get_market_status

# -------- Stage all new data --------
stocks_cache = {}  # ticker -> Stock object
stock_master_tickers = set()
new_stock_master = []
new_indices = []
new_index_holdings = []
new_stocks = []
new_chart_data = {timeframe: [] for timeframe in DB_TIMEFRAMES}

stocks_cache.clear()
stock_master_tickers.clear()
new_stock_master.clear()
new_indices.clear()
new_index_holdings.clear()
new_stocks.clear()
for v in new_chart_data.values():
    v.clear()

# ---- Helper to get Stock object (with chart data) ----
def get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_map):
    if ticker in stocks_cache:
        return stocks_cache[ticker]

    try:
        stock = fetch_stock_data(ticker, now_date, stock_master_map.get(ticker, None), stock_type_map)
        if stock:
            stocks_cache[ticker] = stock
            new_stocks.append(stock)

            # Attach chart data via relationship
            for timeframe, data_list in new_chart_data.items():
                chart_records = fetch_chart_data(stock, timeframe, now_date)
                data_list.extend(chart_records)
        return stock
    except Exception as e:
        print(f"[Fetch Error] {ticker}: {e}")
        return None

def update_stock_master():
    # Delete dead stocks (those not in the new stock master tickers set)
    db.session.execute(
        delete(StockMaster).where(StockMaster.ticker.notin_(stock_master_tickers))
    )

    # Upsert stocks
    for stock in new_stock_master:
        existing = db.session.execute(
            db.select(StockMaster).where(StockMaster.ticker == stock.ticker)
        ).scalar()
        if existing:
            # Update fields
            for attr in stock.attribute_list():
                setattr(existing, attr, getattr(stock, attr))
        else:
            # Insert new stock
            db.session.add(stock)

def clear_stocks_data():
    new_stocks.clear()
    for data_list in new_chart_data.values():
        data_list.clear()

def add_new_stocks_data():
    if new_stocks or any(new_chart_data.values()):
        db.session.add_all(new_stocks)
        for value in new_chart_data.values():
            db.session.add_all(value)
        db.session.flush()

def populate_db(now):
    """
    Populate the database by staging all data first, then replacing
    the main tables in a single atomic transaction.

    - If we store something in the stocks_cache, it means we have already
        inserted the required data for that stock in the database.
    """
    with app.app_context():
        print("Starting Database Population...\n")
        now_date = format_date(now)

        try:
            with db.session.begin():
                print("Deleting Tables...")
                # Delete in FK-safe order
                db.session.execute(delete(IndexHolding))
                db.session.execute(delete(Index))
                db.session.execute(delete(StockMinute))
                db.session.execute(delete(StockHour))
                db.session.execute(delete(StockDay))
                db.session.execute(delete(StockWeek))
                db.session.execute(delete(Stock))
                db.session.flush()
                print("Tables Deleted!")

                # ---- Stock Types Meta ----
                print(f"Updating Stock Type Meta table...")

                stock_types = fetch_stock_types()

                existing = {
                    st.code: st
                    for st in get_all_stock_types()
                }

                for code, desc in stock_types.items():
                    if code in existing:
                        if existing[code].description != desc:
                            existing[code].description = desc
                            existing[code].is_active = True
                    else:
                        db.session.add(
                            StockTypeMeta(code=code, description=desc)
                        )

                # Mark missing ones inactive
                for code, obj in existing.items():
                    if code not in stock_types:
                        obj.is_active = False

                db.session.flush()

                stock_type_map = {
                    st.code: st
                    for st in get_all_stock_types()
                }

                print(f"Updated Stock Type Meta table!")

                # ---- Stock Master ----
                print(f"Fetching data for Stock Master...")
                stocks = fetch_all_stocks_data(stock_type_map)
                for stock in stocks:
                    ticker = stock.ticker
                    if ticker not in stock_master_tickers:
                        stock_master_tickers.add(ticker)
                        new_stock_master.append(stock)
                    else:
                        print(f"Duplicate ticker skipped: {stock.ticker}.")

                print(f"Skipped {len(stocks) - len(new_stock_master)} duplicate tickers.")
                print(f"Total of {len(new_stock_master)} stocks fetched from polygon API!")

                print(f"Flushing Stock Master Table...")
                update_stock_master()

                db.session.flush()

                stock_master_map = {
                    sm.ticker: sm
                    for sm in get_all_stock_master()
                }
                print(f"Flushed Stock Master Table!")

                # ---- Indices and holdings ----
                print(f"Fetching data for indices...")
                with db.session.no_autoflush:
                    for index in all_indices:
                        index_info = get_index_info(index)
                        index_obj = Index(
                            name=index_info.get("name"),
                            slug=index_info.get("slug"),
                            url=index_info.get("url"),
                            last_updated=now
                        )
                        new_indices.append(index_obj)

                        holdings = fetch_index_data(index)
                        for holding in holdings:
                            ticker = holding.get("ticker")
                            if ticker:
                                stock = get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_map)
                                if stock:
                                    index_holding = IndexHolding(
                                        index=index_obj,
                                        stock=stock,
                                        weight=holding.get("weight"),
                                    )
                                    new_index_holdings.append(index_holding)
                        print(f"Fetched data for: {index}!")
                print(f"Fetched data for indices!")

                print("\nFlushing the database with the new fetched data...")
                # Insert new data
                db.session.add_all(new_indices)
                db.session.add_all(new_stocks)
                for value in new_chart_data.values():
                    db.session.add_all(value)
                db.session.add_all(new_index_holdings)

                db.session.flush()
                print("Flushed the database with the new fetched data!\n")


                print("Fetching Trending Stocks data for updated database...")

                # Clearing the collected data to collect data for trending stocks
                clear_stocks_data()

                with db.session.no_autoflush:
                    for stock in get_trending_stocks():
                        ticker = stock.ticker
                        if ticker:
                            get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_map)

                print("Fetched Trending Stocks data for updated database!")

                # Flush Trending Stocks and their chart data
                print("Flushing Trending Stocks data in the database...")
                add_new_stocks_data()
                print("Flushed Trending Stocks data in the database!")


                print("Fetching Top Stocks data for updated database...")

                # Clearing the collected data to collect data for top stocks
                clear_stocks_data()

                with db.session.no_autoflush:
                    for category in get_top_stocks_categories().keys():
                        for stocks_type in ["gainers", "losers", "top_traded"]:
                            for stock in db_get_top_stocks_data(category, stocks_type):
                                ticker = stock.ticker
                                if ticker:
                                    get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_map)

                print("Fetched Top Stocks data for updated database!")

                # Flush Top Stocks and their chart data
                print("Flushing Top Stocks data in the database...")
                add_new_stocks_data()
                print("Flushed Top Stocks data in the database!")


                print("Fetching Search Bar Stocks data for updated database...")

                # Clearing the collected data to collect data for search bar stocks
                clear_stocks_data()

                with db.session.no_autoflush:
                    for item in get_query_stocks(user_query=None).json:
                        ticker = item.get("ticker")
                        if ticker:
                            get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_map)

                print("Fetched Search Bar Stocks data for updated database!")

                # Flush Search Bar Stocks and their chart data
                print("Flushing Search Bar Stocks data in the database...")
                add_new_stocks_data()
                print("Flushed Search Bar Stocks data in the database!")


                # -------- Transactional Replace --------
                print("\nCommiting all the data to the database...")
                # Data will be automatically committed to the database by db.session.begin()
            print("Committed all the data to the database!")

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

        print("\nDatabase Population Completed!\n")

def write_status(now, status):
    status_data = {
        "status": status,
        "last_update_attempted":  format_dt_et(now),
        "last_update_attempted_date": format_date(now)
    }

    if status == "success":
        status_data.update({
            "last_updated": format_dt_et(now),
            "last_updated_date": format_date(now)
        })

    write_to_status_file(filename="populate_db_info.json", status_data=status_data)

def main():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "populate_db"}
    )

    now = get_current_utc()
    write_status(now, status="running")

    try:
        market_status = get_market_status()

        if market_status:
            if market_status == "closed":
                print(f"Market status was {market_status} - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db", "reason": f"market status: {market_status}"}
                )
            else:
                print(f"Market status was {market_status} - proceeding with DB population...")

                populate_db(now)
                write_status(now, status="success")

                app.logger.info(
                    f"Completed script",
                    extra={"log_type": "scheduled_script", "action": "populate_db"}
                )
        else:
            message = "Market status file missing - cannot determine whether to proceed with DB population!"
            print(message)
            raise Exception(message)

    except Exception as e:
        write_status(now, status="failed")
        app.logger.exception(
            f"Script failed",
            extra={"log_type": "scheduled_script", "action": "populate_db", "reason": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
