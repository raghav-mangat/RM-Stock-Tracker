import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from models.database import (
    db, Stock, Index, IndexHolding, StockMaster, StockMinute, StockHour, StockDay, StockWeek,
    StockTypeMeta
)
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import fetch_stock_types, fetch_all_stocks_data, fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES
from data_collectors.market_data import fetch_market_data
from utils.datetime_utils import get_current_utc, format_dt_et, format_date_et
from utils.db_queries.stock_type_meta_data import get_all_stock_types, get_all_active_stock_types
from utils.db_queries.stock_master_data import get_all_stock_master
from utils.db_queries.all_stocks import get_trending_stocks, get_top_stocks_categories, db_get_top_stocks_data
from utils.db_queries.query_stocks import get_query_stocks
from scheduled_scripts.helpers.helpers import write_to_status_file, get_market_status, get_db_populate_info

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
def get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_id_map):
    if ticker in stocks_cache:
        return stocks_cache[ticker]

    try:
        stock = fetch_stock_data(ticker, now_date, stock_master_map.get(ticker, None), stock_type_id_map)
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

def clear_collected_data():
    stock_master_tickers.clear()
    new_stock_master.clear()

    new_indices.clear()
    new_index_holdings.clear()

    new_stocks.clear()
    for data_list in new_chart_data.values():
        data_list.clear()

def populate_db(now):
    """
    Populate the database in separate phases:
    1) Fetch the data for Stock Type Meta table and upsert it in a
        single atomic transaction.
    2) Fetch the data for Stock Master table.
    3) Fetch the data for Stocks, Indices and Holdings.
    4) Upsert Stock Master data, Delete and Insert the Index and
        Stock data into the database in a single atomic transaction.
    5) Fetch the data for Trending Stocks, Top Stocks, and Search
        Bar Stocks.
    6) Insert all of this new Stock data into the database in a
        single atomic transaction.

    - We do this in phases by using separate app context blocks. We do
        this because when we open a connection to the db by accessing it
        by doing a read/write, and start fetching the data which can take
        a long time, the connection gets lost if we access the database
        again in the same app context. Using separate app contexts drops
        and re-initiates a connection to the db. That is why we have large
        fetching data code in separate app context blocks and the db access
        code in separate app context blocks to avoid db connection lost error.
    - We commit the Stock Type Meta table first. If the stock types change
        from massive/polygon API, they would be updated before any other
        stock data is updated in the app. This is an extremely rare
        occurrence and does not harm us right now.
    - We make the stock type ID map and stock master map and use those
        maps to fetch the required data since this allows to have the
        required database data available in memory and not have to query
        the database everytime we need this data.
    - Also, right now we are pre-fetching the stock master stocks and index
        holding stocks before inserting them together in the database.
        The only caveat with this is, lets say a new stock is added by
        massive/polygon in their database, and one of the indices that we
        have contains that stock. Since we are using the un-updated stock
        master stocks in the stock master map, when we fetch the data for
        this new stock, the associated stock master does not exist yet
        since we have not commited the new stock master yet. So we reject
        that stock, and it does not get added in the database. This is alright
        for now since this is a rare occurrence. The alternative to that is to
        commit the stock master table before fetching the Index holdings, but
        that would make the app inconsistent since the overall market data
        would be up to date but the index holdings would not be and the
        last updated timestamp on the website would be inconsistent too.
        Also, since we run this script twice a day, in the second iteration,
        the new stock will be included since we would have the updated stock
        master table. Also, we cannot use the fetched stock master stocks
        in the stock master map to have the updated stocks from massive/
        polygon API because then it gives a stale reference to these ORM
        objects and when we finally insert the data in the database after
        fetching everything it gives us an integrity error.
    - If we store something in the stocks_cache, it means we have already
        collected the required data for that stock.
    """

    print("Starting Database Population...\n")
    now_date = format_date_et(now)

    stock_type_id_map = None
    stock_master_map = None

    with app.app_context():
        # ---- Stock Type Meta ----
        print(f"Fetching data for Stock Type Meta...")

        stock_types = fetch_stock_types()

        print(f"Fetched data for Stock Type Meta!")

        try:
            with db.session.begin():
                print(f"Upserting Stock Type Meta...")

                existing = {
                    st.code: st
                    for st in get_all_stock_types()
                }

                for code, description in stock_types.items():
                    if code in existing:
                        obj = existing[code]
                        if obj.description != description:
                            obj.description = description
                            obj.is_active = True
                    else:
                        db.session.add(
                            StockTypeMeta(
                                code=code,
                                description=description,
                            )
                        )

                for code, obj in existing.items():
                    if code not in stock_types:
                        obj.is_active = False

                # Data will be automatically committed to the database by db.session.begin()

            db.session.commit()
            print(f"Upserted Stock Type Meta!")

            existing.clear()
            stock_type_id_map = {
                st.code: st.id
                for st in get_all_active_stock_types()
            }

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    with app.app_context():
        # ---- Stock Master ----
        print(f"Fetching data for Stock Master...")
        stocks = fetch_all_stocks_data(stock_type_id_map)
        for stock in stocks:
            ticker = stock.ticker
            if ticker not in stock_master_tickers:
                stock_master_tickers.add(ticker)
                new_stock_master.append(stock)
            else:
                print(f"Duplicate ticker skipped: {stock.ticker}.")

        print(f"Skipped {len(stocks) - len(new_stock_master)} duplicate tickers.")
        print(f"Total of {len(new_stock_master)} stocks fetched from polygon API!")

        all_stock_master = get_all_stock_master()
        if not all_stock_master:
            all_stock_master = new_stock_master

        stock_master_map = {
            sm.ticker: sm
            for sm in all_stock_master
        }

    with app.app_context():
        # ---- Indices and holdings ----
        print(f"Fetching data for indices...")
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
                    stock = get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_id_map)
                    if stock:
                        index_holding = IndexHolding(
                            index=index_obj,
                            stock=stock,
                            weight=holding.get("weight"),
                        )
                        new_index_holdings.append(index_holding)
            print(f"Fetched data for: {index}!")
        print(f"Fetched data for indices!")

    with app.app_context():
        try:
            with db.session.begin():
                print("\nStaring transactional replace...")

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
                print("Deleted Tables!")

                print(f"Flushing Stock Master...")
                update_stock_master()

                db.session.flush()
                print(f"Flushed Stock Master!")

                print("Flushing Stock, Index, Index Holdings...")
                # Insert new data
                db.session.add_all(new_indices)
                db.session.add_all(new_stocks)
                for value in new_chart_data.values():
                    db.session.add_all(value)
                db.session.add_all(new_index_holdings)

                db.session.flush()
                print("Flushed Stock, Index, Index Holdings!")

                # -------- Transactional Replace --------
                print("\nCommiting all the data to the database...")
                # Data will be automatically committed to the database by db.session.begin()

            db.session.commit()
            print("\nCompleted transactional replace!")

            # Clearing the collected data to collect some more data to
            # store in the database
            clear_collected_data()

            # Create the new stock master map with the updated StockMaster table
            stock_master_map.clear()
            stock_master_map = {
                sm.ticker: sm
                for sm in get_all_stock_master()
            }

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    with app.app_context():
        print("Fetching Trending Stocks data for updated database...")
        for stock in get_trending_stocks():
            ticker = stock.ticker
            if ticker:
                get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_id_map)
        print("Fetched Trending Stocks data for updated database!")

        print("Fetching Top Stocks data for updated database...")
        for category in get_top_stocks_categories().keys():
            for stocks_type in ["gainers", "losers", "top_traded"]:
                for stock in db_get_top_stocks_data(category, stocks_type):
                    ticker = stock.ticker
                    if ticker:
                        get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_id_map)
        print("Fetched Top Stocks data for updated database!")

        print("Fetching Search Bar Stocks data for updated database...")
        for item in get_query_stocks(user_query=None).json:
            ticker = item.get("ticker")
            if ticker:
                get_or_fetch_stock(ticker, now_date, stock_master_map, stock_type_id_map)
        print("Fetched Search Bar Stocks data for updated database!")

    with app.app_context():
        try:
            with db.session.begin():
                print("\nAdding more data to the database...")

                # Add the new data into the database
                if new_stocks or any(new_chart_data.values()):
                    db.session.add_all(new_stocks)
                    for value in new_chart_data.values():
                        db.session.add_all(value)

                print("\nCommiting the new data to the database...")
                # Data will be automatically committed to the database by db.session.begin()

            db.session.commit()
            print("\nAdded more data to the database!")

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    print("\nDatabase Population Completed!\n")

def write_status(now, status):
    status_data = {
        "status": status,
        "last_update_attempted":  format_dt_et(now),
        "last_update_attempted_date": format_date_et(now)
    }

    if status == "success":
        status_data.update({
            "last_updated": format_dt_et(now),
            "last_updated_date": format_date_et(now)
        })

    write_to_status_file(filename="populate_db_info.json", status_data=status_data)

def main():
    """
    We run this script twice every day. First when the market closes
    at 4 pm ET and second after the market closing tasks have been
    completed at 8 pm ET. Since the market time follows ET, we have
    to factor in daylight savings. Since we schedule this script
    in UTC, we schedule it twice for the first iteration at 4 pm ET.
    We have 1-hour difference between these 2 scheduled times.
    This is why we have so many conditions to check before we actually
    populate the db.
    """

    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "populate_db"}
    )

    now = get_current_utc()
    now_date = format_date_et(now)

    try:
        stored_market_status = get_market_status()

        current_market_data = fetch_market_data()
        current_market_status = current_market_data.get("market_status") if current_market_data else None

        db_populate_info = get_db_populate_info()
        db_last_updated_date = db_populate_info.get("last_updated_date")
        db_populate_status = db_populate_info.get("status")

        if stored_market_status and current_market_status:
            if stored_market_status == "closed":
                print(f"Market status was {stored_market_status} - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db", "reason": f"market status: {stored_market_status}"}
                )
            elif current_market_status == "open":
                print(f"Current market status was {current_market_status} - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db",
                           "reason": f"current market status: {current_market_status}"}
                )
            elif db_last_updated_date == now_date:
                print(f"DB already populated - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db",
                           "reason": f"DB already populated"}
                )
            elif db_populate_status == "running":
                print(f"DB population already in progress - skipping DB population!")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db",
                           "reason": f"DB population already in progress"}
                )
            else:
                print(f"Market status was {stored_market_status} - proceeding with DB population...")

                write_status(now, status="running")
                populate_db(now)
                write_status(now, status="success")

                app.logger.info(
                    f"Completed script",
                    extra={"log_type": "scheduled_script", "action": "populate_db"}
                )
        else:
            message = "Market status files missing - cannot determine whether to proceed with DB population!"
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
