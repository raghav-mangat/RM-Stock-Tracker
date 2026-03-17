import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from models.database import (
    db, Index, IndexHolding, StockTypeMeta, TickerMaster, DatasetVersion, StockDetail, StockMaster
)
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import (
    fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES,
    fetch_full_market_snapshot_data, fetch_all_tickers_data,
    fetch_stock_types, get_stock_master_data, get_stock_detail_data
)
from utils.datetime_utils import get_current_utc, get_current_et, format_dt_et, format_date_et
from utils.db_queries.tables.ticker_master import get_all_active_ticker_master
from utils.db_queries.tables.stock_type_meta import get_all_stock_types, get_all_active_stock_types
from utils.db_queries.tables.stock_master import get_all_stock_master_by_dataset_version
from utils.db_queries.all_stocks import get_trending_stocks, get_top_stocks_categories, db_get_top_stocks_data
from utils.db_queries.query_stocks import get_query_stocks
from scheduled_scripts.helpers.helpers import write_to_status_file, get_market_status


BATCH_SIZE = 1000

# -------- Stage all new data --------
stocks_cache = {}  # ticker -> Stock object
new_stocks = []
new_chart_data = {timeframe: [] for timeframe in DB_TIMEFRAMES}

stocks_cache.clear()
new_stocks.clear()
for v in new_chart_data.values():
    v.clear()

# ---- Helper to get Stock object (with chart data) ----
def get_or_fetch_stock(ticker, now_date, stock_master_map):
    stock = None

    if ticker in stocks_cache:
        stock = stocks_cache[ticker]
    else:
        try:
            stock = fetch_stock_data(stock_master=stock_master_map.get(ticker, None), now=now_date)
            if stock:
                stocks_cache[ticker] = stock
                new_stocks.append(stock)

                # Attach chart data via relationship
                for timeframe, data_list in new_chart_data.items():
                    chart_records = fetch_chart_data(stock, timeframe, now_date)
                    data_list.extend(chart_records)

        except Exception as e:
            print(f"[Fetch Error] {ticker}: {e}")

    return stock

def update_ticker_master(full_market_snapshot_data, all_tickers_data):
    print(f"\n---- Updating Ticker Master...")

    tickers = set(full_market_snapshot_data).intersection(set(all_tickers_data))
    print(f"Number of Ticker Master: {len(tickers)}")

    # Abort if no ticker master data is received from Massive API,
    if not tickers:
        raise Exception("No tickers received from Massive API")

    tickers = {t.upper() for t in tickers}

    try:
        with db.session.begin():
            # Mark inactive tickers
            db.session.execute(
                db.update(TickerMaster)
                .where(
                    ~TickerMaster.symbol.in_(tickers),
                    TickerMaster.is_active == True
                )
                .values(is_active=False)
            )

            # Activate any tickers in the new list
            db.session.execute(
                db.update(TickerMaster)
                .where(
                    TickerMaster.symbol.in_(tickers),
                    TickerMaster.is_active == False
                )
                .values(is_active=True)
            )

            # Fetch existing tickers as set for upsert comparison
            existing_symbols = set(
                db.session.execute(db.select(TickerMaster.symbol)).scalars().all()
            )

            # Insert new tickers
            tickers_to_add = tickers - existing_symbols
            if tickers_to_add:
                ticker_master_data = [
                    {"symbol": symbol}
                    for symbol in tickers_to_add
                ]
                for i in range(0, len(ticker_master_data), BATCH_SIZE):
                    chunk = ticker_master_data[i:i + BATCH_SIZE]
                    db.session.bulk_insert_mappings(TickerMaster, chunk)

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print(f"---- Updated Ticker Master!")

def update_stock_type_meta(stock_types):
    print(f"\n---- Updating Stock Type Meta...")

    # Abort if no stock types data is received from Massive API
    if not stock_types:
        raise Exception("No stock types data received from Massive API")

    # Upsert Stock Type Meta
    try:
        with db.session.begin():
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

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print(f"---- Updated Stock Type Meta!")

def update_stock_detail(all_tickers_data, ticker_id_map, stock_type_id_map):
    print(f"\n---- Updating Stock Detail...")

    stock_detail_data = get_stock_detail_data(all_tickers_data, ticker_id_map, stock_type_id_map)

    # Abort if no stock detail data is received from Massive API
    if not stock_detail_data:
        raise Exception("No stock detail data received from Massive API")

    try:
        with db.session.begin():
            db.session.execute(delete(StockDetail))
            db.session.flush()
            for i in range(0, len(stock_detail_data), BATCH_SIZE):
                chunk = stock_detail_data[i:i + BATCH_SIZE]
                db.session.bulk_insert_mappings(StockDetail, chunk)

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print(f"---- Updated Stock Detail!")

def update_stock_master(full_market_snapshot_data, ticker_id_map, dataset_version_id):
    print(f"\n---- Updating Stock Master...")

    stock_master_data = get_stock_master_data(full_market_snapshot_data, ticker_id_map, dataset_version_id)

    # Abort if no stock master data is received from Massive API
    if not stock_master_data:
        raise Exception("No stock master data received from Massive API")

    try:
        with db.session.begin():
            for i in range(0, len(stock_master_data), BATCH_SIZE):
                chunk = stock_master_data[i:i + BATCH_SIZE]
                db.session.bulk_insert_mappings(StockMaster, chunk)

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print(f"---- Updated Stock Master!")

def update_stock_index_data(now, now_date, stock_master_map, dataset_version_id):
    new_indices = []
    new_index_holdings = []
    index_holdings_temp = []

    with app.app_context():
        # ---- Indices and holdings ----
        print(f"\n---- Fetching data for indices...")
        for index in all_indices:
            index_info = get_index_info(index)
            index_obj = Index(
                name=index_info.get("name"),
                slug=index_info.get("slug"),
                url=index_info.get("url"),
                last_updated=now,
                dataset_version_id=dataset_version_id
            )
            new_indices.append(index_obj)

            holdings = fetch_index_data(index)
            for holding in holdings:
                ticker = holding.get("ticker")
                if ticker:
                    stock = get_or_fetch_stock(ticker, now_date, stock_master_map)
                    if stock:
                        index_holdings_temp.append(
                            (index_obj, stock, holding.get("weight"))
                        )

            print(f"Fetched data for: {index}!")
        print(f"---- Fetched data for indices!")

    with app.app_context():
        print("\n---- Adding Fetched Data...")
        try:
            with db.session.begin():
                db.session.add_all(new_indices)
                db.session.add_all(new_stocks)
                db.session.flush()

                for value in new_chart_data.values():
                    for i in range(0, len(value), BATCH_SIZE):
                        chunk = value[i:i + BATCH_SIZE]
                        db.session.bulk_save_objects(chunk)

                for index_obj, stock_obj, weight in index_holdings_temp:
                    new_index_holdings.append(
                        IndexHolding(
                            index_id=index_obj.id,
                            stock_id=stock_obj.id,
                            weight=weight
                        )
                    )

                for i in range(0, len(new_index_holdings), BATCH_SIZE):
                    chunk = new_index_holdings[i:i + BATCH_SIZE]
                    db.session.bulk_save_objects(chunk)

                # Data will be automatically committed to the database by db.session.begin()

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

        print("---- Added Fetched Data!")

def update_additional_stock_data(now_date, stock_master_map, dataset_version_id):
    print("\n---- Fetching Additional Stock Data for updated database...")
    with app.app_context():
        print("Fetching Trending Stocks data for updated database...")
        for stock in get_trending_stocks(dataset_version_id):
            ticker = stock.ticker
            if ticker:
                get_or_fetch_stock(ticker, now_date, stock_master_map)
        print("Fetched Trending Stocks data for updated database!")

    with app.app_context():
        print("Fetching Top Stocks data for updated database...")
        for category in get_top_stocks_categories().keys():
            for stocks_type in ["gainers", "losers", "top_traded"]:
                for stock in db_get_top_stocks_data(category, stocks_type, dataset_version_id):
                    ticker = stock.ticker
                    if ticker:
                        get_or_fetch_stock(ticker, now_date, stock_master_map)
        print("Fetched Top Stocks data for updated database!")

    with app.app_context():
        print("Fetching Search Bar Stocks data for updated database...")
        for item in get_query_stocks(user_query=None, dataset_version_id=dataset_version_id).json:
            ticker = item.get("ticker")
            if ticker:
                get_or_fetch_stock(ticker, now_date, stock_master_map)
        print("Fetched Search Bar Stocks data for updated database!")

    print("---- Fetched Additional Stock Data for updated database!")

    with app.app_context():
        print("\n---- Updating Additional Data...")
        try:
            with db.session.begin():
                db.session.add_all(new_stocks)
                db.session.flush()

                for value in new_chart_data.values():
                    for i in range(0, len(value), BATCH_SIZE):
                        chunk = value[i:i + BATCH_SIZE]
                        db.session.bulk_save_objects(chunk)

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

        print("---- Updated Additional Data!")

def create_new_dataset_version(now):
    dataset_version_id = None
    try:
        with db.session.begin():
            new_dataset_version = DatasetVersion(
                is_active=False,
                last_updated=now
            )
            db.session.add(new_dataset_version)
            db.session.flush()

            dataset_version_id = new_dataset_version.id

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    return dataset_version_id

def update_dataset_version(dataset_version_id):
    print(f"\n---- Updating Dataset Version...")
    try:
        with db.session.begin():
            db.session.execute(
                db.update(DatasetVersion)
                .where(DatasetVersion.is_active == True)
                .values(is_active=False)
            )

            db.session.execute(
                db.update(DatasetVersion)
                .where(DatasetVersion.id == dataset_version_id)
                .values(is_active=True)
            )

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print(f"---- Updated Dataset Version!")

def delete_old_data():
    print("\n---- Deleting Old Data...")

    try:
        with db.session.begin():
            db.session.execute(
                db.delete(DatasetVersion)
                .where(DatasetVersion.is_active == False)
            )

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    print("---- Deleted Old Data!")

def populate_db(now):
    """
    - Populate the database in separate phases.
    - We first fetch the data for all the stocks from Massive API. Using
        that data we update the Ticker Master table. We create a new dataset
        version which we do not make active yet. We use this new version to fetch
        the data for Stock Master, Stocks, Index, Holdings etc. and insert
        this data into the database. Since this dataset version is not active
        yet, the users still see the previous active dataset version data on
        the platform even though we have the new data inserted into the database.
        We then update the Stock Type Meta and Stock Detail tables with the
        new data and the users see these changes instantly since it is not
        linked to a specific dataset version which is alright since this
        data is rarely changed anyway even though it is not exactly consistent
        with the last updated time being shown to the user which we get from the
        Stock Master. But as soon as this is updated we also update the Dataset
        Version making this new one the active one so now the users see the most
        up-to-date data, so this inconsistency between Stock Detail and Stock
        Master exists for a very short time. We then delete the inactive dataset
        versions which cascades the database to delete all the related data for
        that version cleaning up the old non-required data.
    - Ticker Master table is the main table in our database that keeps
        track of all tickers available on our platform. The Watchlist Items
        are also dependent on this table. If this table is deleted all the
        user watchlist data along with all stocks data available on the
        platform will be deleted. So be careful while updating this table.
        This table contains the set intersection of all stocks received from
        all tickers and full market snapshot Massive API endpoints. Before doing
        this intersection we also filter out all the stocks for which the API
        returns None for any required attribute to get rid of stocks that have
        incomplete data. When we update this table we just set the tickers as
        inactive if they are not present in the new tickers fetched from
        Massive API instead of deleting them. Then we query only the active
        tickers. Right now when the Ticker Master becomes inactive the ticker
        still remains as user watchlist item but is not shown to the user.
    - For the additional stocks data like the trending, top stocks etc., we
        use the new dataset version to query the updated stocks and save it
        in the database pre-hand before updating the dataset version.
    - We do this in phases by using separate app context blocks. We do
        this because when we open a connection to the db by accessing it
        by doing a read/write, and start fetching the data which can take
        a long time, the connection gets lost if we access the database
        again in the same app context. Using separate app contexts drops
        and re-initiates a connection to the db. That is why we have large
        fetching data code in separate app context blocks and the db access
        code in separate app context blocks to avoid db connection lost error.
    - We make the ticker ID map, stock type ID map and stock master map and
        use those maps to fetch the required data since this allows to have
        the required database data available in memory and not have to query
        the database everytime we need this data.
    - We also try to insert the data into the database in bulk and in chunks
        to make the inserts fast and efficient. If a transaction takes a long
        time to complete it either slows down the platform or just does not
        allow user changes to take place if an associated database table is
        being updated for example updating the watchlist items.
    - If we store something in the stocks_cache, it means we have already
        collected the required data for that stock.
    """

    print("Starting Database Population...\n")

    full_market_snapshot_data = dict()
    all_tickers_data = dict()
    stock_types = dict()

    ticker_id_map = dict()
    stock_type_id_map = dict()
    stock_master_map = dict()

    dataset_version_id = None

    with app.app_context():
        print(f"\n---- Fetching data from Massive API...")
        full_market_snapshot_data = fetch_full_market_snapshot_data()
        all_tickers_data = fetch_all_tickers_data()
        stock_types = fetch_stock_types()

        # Abort if no data received from Massive API
        if not (full_market_snapshot_data and all_tickers_data and stock_types):
            raise Exception("Incomplete data received from Massive API")

        print(f"---- Fetched data from Massive API!")

    with app.app_context():
        update_ticker_master(full_market_snapshot_data, all_tickers_data)

        ticker_id_map = {
            ticker.symbol: ticker.id
            for ticker in get_all_active_ticker_master()
        }

    with app.app_context():
        dataset_version_id = create_new_dataset_version(now)

    with app.app_context():
        update_stock_master(full_market_snapshot_data, ticker_id_map, dataset_version_id)

        stock_master_map = {
            sm.ticker.symbol: sm
            for sm in get_all_stock_master_by_dataset_version(dataset_version_id)
        }

    now_date = format_date_et(now)
    update_stock_index_data(now, now_date, stock_master_map, dataset_version_id)

    new_stocks.clear()
    for val in new_chart_data.values():
        val.clear()

    update_additional_stock_data(now_date, stock_master_map, dataset_version_id)

    with app.app_context():
        update_stock_type_meta(stock_types)

        stock_type_id_map = {
            st.code: st.id
            for st in get_all_active_stock_types()
        }

    with app.app_context():
        update_stock_detail(all_tickers_data, ticker_id_map, stock_type_id_map)

    with app.app_context():
        update_dataset_version(dataset_version_id)

    with app.app_context():
        delete_old_data()

    print("\n\nDatabase Population Completed!\n")

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
    in UTC, we schedule it twice everytime we need to run the script.
    We have 1-hour difference between these 2 scheduled times.
    This is why we have the conditions to check before we actually
    populate the db.
    """

    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "populate_db"}
    )

    now = get_current_utc()

    current_et_hour = get_current_et().hour

    try:
        stored_market_status = get_market_status()

        if stored_market_status:
            if stored_market_status == "closed":
                print(f"Market status was {stored_market_status} - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db", "reason": f"market status: {stored_market_status}"}
                )
            elif current_et_hour not in [16, 20]:
                print(f"Not in the correct time slot - skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db",
                           "reason": f"Not in the correct time slot"}
                )
            else:
                print(f"Market status was {stored_market_status} - proceeding with DB population!")

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
