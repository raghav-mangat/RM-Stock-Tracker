import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from sqlalchemy import delete
from sqlalchemy.orm import joinedload
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from models.database import (
    db, Index, IndexHolding, StockTypeMeta, TickerMaster, DatasetVersion,
    StockDetail, StockMaster, Stock
)
from data_collectors.market_data import fetch_market_status
from data_collectors.index_data import all_indices, get_index_info, fetch_index_data
from data_collectors.stock_data import (
    fetch_stock_data, fetch_chart_data, DB_TIMEFRAMES,
    fetch_full_market_snapshot_data, fetch_all_tickers_data,
    fetch_stock_types, get_stock_master_data, get_stock_detail_data
)
from utils.datetime_utils import get_current_utc, format_dt_et, format_date_et, get_current_et
from utils.db_queries.tables.ticker_master import get_all_active_ticker_master
from utils.db_queries.tables.dataset_version import get_active_dataset_market_status
from utils.db_queries.tables.stock_type_meta import get_all_stock_types, get_all_active_stock_types
from utils.db_queries.tables.stock_master import get_all_stock_master_by_dataset_version
from utils.db_queries.all_stocks import get_trending_stocks, get_top_stocks_categories, db_get_top_stocks_data
from utils.db_queries.query_stocks import get_query_stocks
from utils.status_files import write_to_status_file


BATCH_SIZE = 1000
MAX_WORKERS = min(32, (os.cpu_count() or 4) * 8)

def update_ticker_master(full_market_snapshot_data, all_tickers_data):
    print(f"\n---- Updating Ticker Master...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Updated Ticker Master!")

def update_stock_type_meta(stock_types):
    print(f"\n---- Updating Stock Type Meta...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Updated Stock Type Meta!")

def update_stock_detail(all_tickers_data, ticker_id_map, stock_type_id_map):
    print(f"\n---- Updating Stock Detail...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Updated Stock Detail!")

def update_stock_master(full_market_snapshot_data, ticker_id_map, dataset_version_id):
    print(f"\n---- Updating Stock Master...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Updated Stock Master!")

def get_and_update_indices_data(now, dataset_version_id):
    tickers = set()
    new_indices = []
    index_holdings_temp = []

    print(f"\n---- Getting data for indices...")
    start_time = time.perf_counter()

    index_map = {}  # slug -> Index object

    # Indices and holdings
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
        index_map[index] = index_obj

    # Parallel fetch holdings
    def worker(index_):
        holdings_ = fetch_index_data(index_)
        return index_, holdings_

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(worker, index) for index in all_indices]

        for future in as_completed(futures):
            index, holdings = future.result()
            index_obj = index_map.get(index)

            for holding in holdings:
                ticker = holding.get("ticker")
                if ticker:
                    tickers.add(ticker)
                    index_holdings_temp.append(
                        (index_obj.slug, ticker, holding.get("weight"))
                    )

            print(f"Got data for: {index}!")

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Got data for indices!")

    print("\n---- Updating Indices Data...")
    start_time = time.perf_counter()

    with app.app_context():
        try:
            with db.session.begin():
                for i in range(0, len(new_indices), BATCH_SIZE):
                    chunk = new_indices[i:i + BATCH_SIZE]
                    db.session.bulk_save_objects(chunk)

                # Data will be automatically committed to the database by db.session.begin()

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Updated Indices Data!")

    return tickers, index_holdings_temp

def get_additional_stock_data(tickers, dataset_version_id):
    print("\n---- Getting Additional Stock Data for updated database...")
    start_time = time.perf_counter()

    with app.app_context():
        print("Getting Trending Stocks data for updated database...")
        for stock in get_trending_stocks(dataset_version_id):
            ticker = stock.ticker
            if ticker:
                tickers.add(ticker)
        print("Got Trending Stocks data for updated database!")

        print("Getting Top Stocks data for updated database...")
        for category in get_top_stocks_categories().keys():
            for stocks_type in ["gainers", "losers", "top_traded"]:
                for stock in db_get_top_stocks_data(category, stocks_type, dataset_version_id):
                    ticker = stock.ticker
                    if ticker:
                        tickers.add(ticker)
        print("Got Top Stocks data for updated database!")

        print("Getting Search Bar Stocks data for updated database...")
        for item in get_query_stocks(user_query=None, dataset_version_id=dataset_version_id).json:
            ticker = item.get("ticker")
            if ticker:
                tickers.add(ticker)
        print("Got Search Bar Stocks data for updated database!")

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Got Additional Stock Data for updated database!")

    return tickers

def fetch_and_update_stock_data(tickers, stock_master_map, now_date):
    print("\n---- Fetching Stocks Data...")
    start_time = time.perf_counter()

    with app.app_context():
        stocks = parallel_fetch_stocks(tickers, stock_master_map, now_date)

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Fetched Stocks Data!")

    print("\n---- Updating Stocks Data...")
    start_time = time.perf_counter()

    with app.app_context():
        try:
            with db.session.begin():
                for i in range(0, len(stocks), BATCH_SIZE):
                    chunk = stocks[i:i + BATCH_SIZE]
                    db.session.bulk_save_objects(chunk)

                # Data will be automatically committed to the database by db.session.begin()

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Updated Stocks Data!")

def fetch_and_update_chart_data(now_date, dataset_version_id):
    print("\n---- Fetching Chart Data...")
    start_time = time.perf_counter()

    with app.app_context():
        stocks = (
            db.session.query(Stock)
            .options(
                joinedload(Stock.stock_master)
                .joinedload(StockMaster.ticker)
            )
            .join(StockMaster)
            .filter(StockMaster.dataset_version_id == dataset_version_id)
        ).all()

    with app.app_context():
        all_chart_data = parallel_fetch_charts(stocks, now_date)

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Fetched Chart Data!")

    print("\n---- Updating Chart Data...")
    start_time = time.perf_counter()

    with app.app_context():
        try:
            with db.session.begin():
                for value in all_chart_data.values():
                    for i in range(0, len(value), BATCH_SIZE):
                        chunk = value[i:i + BATCH_SIZE]
                        db.session.bulk_save_objects(chunk)

                # Data will be automatically committed to the database by db.session.begin()

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Updated Chart Data!")

def update_index_holdings_data(index_holdings_temp, dataset_version_id):
    new_index_holdings = []

    print("\n---- Updating Index Holdings Data...")
    start_time = time.perf_counter()

    with app.app_context():
        indices = (
            db.session.query(
                Index.slug,
                Index.id
            )
            .select_from(Index)
            .filter(
                Index.dataset_version_id == dataset_version_id
            )
        ).all()

        stocks = (
            db.session.query(
                TickerMaster.symbol.label("ticker"),
                Stock.id
            )
            .select_from(Stock)
            .join(StockMaster)
            .join(TickerMaster)
            .filter(
                TickerMaster.is_active == True,
                StockMaster.dataset_version_id == dataset_version_id
            )
        ).all()

    indices_map = {
        index.slug: index.id
        for index in indices
    }

    stocks_map = {
        stock.ticker: stock.id
        for stock in stocks
    }

    for slug, ticker, weight in index_holdings_temp:
        index_id = indices_map.get(slug, None)
        stock_id = stocks_map.get(ticker, None)
        if index_id and stock_id:
            new_index_holdings.append({
                "index_id": index_id,
                "stock_id": stock_id,
                "weight": weight
            })

    with app.app_context():
        try:
            with db.session.begin():
                for i in range(0, len(new_index_holdings), BATCH_SIZE):
                    chunk = new_index_holdings[i:i + BATCH_SIZE]
                    db.session.bulk_insert_mappings(IndexHolding, chunk)

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Updated Index Holdings Data!")

def fetch_stock_worker(ticker, stock_master_map, now_date):
    stock = None

    stock_master = stock_master_map.get(ticker)
    if stock_master:
        stock = fetch_stock_data(stock_master=stock_master, now=now_date)

    return stock

def parallel_fetch_stocks(tickers, stock_master_map, now_date):
    stocks = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_stock_worker, ticker, stock_master_map, now_date)
            for ticker in tickers
        ]

        for future in as_completed(futures):
            stock = future.result()
            if stock:
                stocks.append(stock)

    return stocks

def fetch_chart_worker(stock, now_date):
    chart_data = {tf: [] for tf in DB_TIMEFRAMES}

    for timeframe in DB_TIMEFRAMES:
        records = fetch_chart_data(stock, timeframe, now_date)
        chart_data[timeframe].extend(records)

    return chart_data

def parallel_fetch_charts(stocks, now_date):
    all_chart_data = {tf: [] for tf in DB_TIMEFRAMES}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_chart_worker, stock, now_date)
            for stock in stocks
        ]

        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue

            for tf, data in result.items():
                all_chart_data[tf].extend(data)

    return all_chart_data

def create_new_dataset_version(now, market_status):
    print(f"\n---- Creating Dataset Version...")
    start_time = time.perf_counter()

    dataset_version_id = None
    try:
        with db.session.begin():
            new_dataset_version = DatasetVersion(
                is_active=False,
                last_updated=now,
                market_status=market_status
            )
            db.session.add(new_dataset_version)
            db.session.flush()

            dataset_version_id = new_dataset_version.id

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        raise

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Created Dataset Version!")

    return dataset_version_id

def update_dataset_version(dataset_version_id):
    print(f"\n---- Updating Dataset Version...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print(f"---- Updated Dataset Version!")

def delete_old_data():
    print("\n---- Deleting Old Data...")
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    print(f"-Time: {end_time - start_time:.4f} seconds")
    print("---- Deleted Old Data!")

def populate_db(now, market_status):
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
    - We use threading to fetch the data from Massive API and data for indices
        to speed up the fetching process alot.
    """

    print("Starting Database Population...\n")
    populate_start_time = time.perf_counter()

    full_market_snapshot_data = dict()
    all_tickers_data = dict()
    stock_types = dict()

    ticker_id_map = dict()
    stock_type_id_map = dict()
    stock_master_map = dict()

    dataset_version_id = None

    with app.app_context():
        print(f"\n---- Fetching data from Massive API...")
        start_time = time.perf_counter()

        full_market_snapshot_data = fetch_full_market_snapshot_data()
        all_tickers_data = fetch_all_tickers_data()
        stock_types = fetch_stock_types()

        # Abort if no data received from Massive API
        if not (full_market_snapshot_data and all_tickers_data and stock_types):
            raise Exception("Incomplete data received from Massive API")

        end_time = time.perf_counter()
        print(f"-Time: {end_time - start_time:.4f} seconds")
        print(f"---- Fetched data from Massive API!")

    with app.app_context():
        update_ticker_master(full_market_snapshot_data, all_tickers_data)

        ticker_id_map = {
            ticker.symbol: ticker.id
            for ticker in get_all_active_ticker_master()
        }

    with app.app_context():
        dataset_version_id = create_new_dataset_version(now, market_status)

    with app.app_context():
        update_stock_master(full_market_snapshot_data, ticker_id_map, dataset_version_id)

        stock_master_map = {
            sm.ticker.symbol: sm
            for sm in get_all_stock_master_by_dataset_version(dataset_version_id)
        }

    now_date = format_date_et(now)

    tickers, index_holdings_temp = get_and_update_indices_data(now, dataset_version_id)

    tickers = get_additional_stock_data(tickers, dataset_version_id)

    fetch_and_update_stock_data(tickers, stock_master_map, now_date)

    fetch_and_update_chart_data(now_date, dataset_version_id)

    update_index_holdings_data(index_holdings_temp, dataset_version_id)

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

    populate_end_time = time.perf_counter()
    print(f"\n\n-Total Time: {populate_end_time - populate_start_time:.4f} seconds")
    print("Database Population Completed!\n")

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

    with app.app_context():
        write_to_status_file(filename="db_populate_status.json", status_data=status_data)

def main():
    """
    - We run this script hourly every day, and also at 9:30 am
        ET when the market opens.
    - We first check the ET minute at 9th ET hour to make sure the
        script only runs after the 30th minute when the market is
        open.
    - We also check if the current ET hour is in the selected
        market hours. We are only running at these hours since
        running this script takes alot of CPU seconds, and we
        would need to buy more to make it run more frequently.
        Right now we run it in the selected hours since the
        market is open at that time and once when the market is
        closed to get the closing data.
    - Before running we check the current market status. If the
        market is not closed then always run it. If the market is
        closed check the market status when we last updated the
        database by looking at the active dataset version.
        If the status was not closed then it means we did not run it
        one last time to get the final closed market data for the day.
        So run it one last time store the closed market data for the
        day and then the script runs when the market is not closed next.
    - This is why we have the conditions to check before we actually
        run the script.
    """

    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "populate_db"}
    )

    now = get_current_utc()

    current_et = get_current_et()
    current_et_hour = current_et.hour
    current_et_minute = current_et.minute
    should_skip = False

    # Check the time slot
    selected_market_hours = [11, 12, 13, 14, 15, 16, 20]
    if current_et_hour == 9:
        if current_et_minute < 30:
            should_skip = True
    elif current_et_hour not in selected_market_hours:
        should_skip = True

    if should_skip:
        message = "Not in the correct time slot"
        print(f"{message} - Skipping DB population!")
        write_status(now, status="skipped")
        app.logger.info(
            f"Skipping script",
            extra={"log_type": "scheduled_script", "action": "populate_db",
                   "reason": f"{message}"}
        )
        return

    try:
        with app.app_context():
            market_status = fetch_market_status()
            current_market_status = market_status.get("market", None) if market_status else None
            active_dataset_market_status = get_active_dataset_market_status() or ""

        if current_market_status:
            message = (f"Current market status: {current_market_status}, Active dataset market status: "
                      f"{active_dataset_market_status}")
            if (current_market_status != "closed"
                    or (current_market_status == "closed" and active_dataset_market_status != "closed")):
                print(f"{message} - Proceeding with DB population!")

                write_status(now, status="running")
                populate_db(now, current_market_status)
                write_status(now, status="success")

                app.logger.info(
                    f"Completed script",
                    extra={"log_type": "scheduled_script", "action": "populate_db"}
                )

            else:
                print(f"{message} - Skipping DB population!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "populate_db",
                           "reason": f"{message}"}
                )
        else:
            message = "Market status missing - Cannot determine whether to proceed with DB population!"
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
