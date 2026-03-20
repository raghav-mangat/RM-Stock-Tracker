from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import os
from metrics import metrics
from metrics.registry import MetricName
from models.database import Stock, StockMinute, StockHour, StockDay, StockWeek
from utils.datetime_utils import (
    polygon_timestamp_to_utc_dt, format_date, DATE_FORMAT, DATETIME_FORMAT,
    utc_dt_to_polygon_timestamp
)
from utils.populate_db_info import db_last_updated_date
from utils.db_queries.tables.stock_type_meta import get_stock_type_id_by_code

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
client = RESTClient(POLYGON_API_KEY)

# List of all attributes that we store in the database for all stocks available in Polygon API.
# Must be the same as all the fields in the Stock Master table in the database.
FULL_MARKET_SNAPSHOT_ATTRIBUTES = [
    "last_updated", "day_close", "day_open", "day_high", "day_low", "volume",
    "vwap", "todays_change", "todays_change_perc",
    "prev_o", "prev_h", "prev_l", "prev_c", "prev_v", "prev_vwap",
]
STOCK_MASTER_ATTRIBUTES = FULL_MARKET_SNAPSHOT_ATTRIBUTES + [
    "ticker_id", "dataset_version_id", "popularity"
]

# Must be the same as all the fields in the Stock Detail table in the database.
ALL_TICKERS_ATTRIBUTES = [
    "name", "primary_exchange", "stock_type_code",
]
STOCK_DETAIL_ATTRIBUTES = [
    "ticker_id", "name", "primary_exchange", "stock_type_id",
]

# List of all attributes that we store in the database for a given stock.
# Must be the same as all the fields in the Stock table in the database.
STOCK_ATTRIBUTES = [
    "description", "homepage_url", "list_date", "industry", "total_employees",
    "market_cap", "icon_url",
    "dma_30", "dma_50", "dma_200", "dma_30_perc_diff", "dma_50_perc_diff", "dma_200_perc_diff",
    "high_52w", "low_52w", "high_52w_perc_diff", "low_52w_perc_diff",
    "related_companies", "stock_master_id"
]

TIMEFRAME_OPTIONS = {
    "1D": {
        "timespan": "minute",
        "before": lambda now: now,
        "date_format": DATETIME_FORMAT,
        "ema_data": True,
    },
    "1W": {
        "timespan": "hour",
        "before": lambda now: now - timedelta(days=7),
        "date_format": DATETIME_FORMAT,
        "ema_data": True,
    },
    "1M": {
        "timespan": "day",
        "before": lambda now: now - timedelta(days=30),
        "date_format": DATE_FORMAT,
        "ema_data": True,
    },
    "3M": {
        "timespan": "day",
        "before": lambda now: now - timedelta(days=30*3),
        "date_format": DATE_FORMAT,
        "ema_data": True,
    },
    "6M": {
        "timespan": "day",
        "before": lambda now: now - timedelta(days=30*6),
        "date_format": DATE_FORMAT,
        "ema_data": True,
    },
    "YTD": {
        "timespan": "day",
        "before": lambda now: datetime(now.year, 1, 1),
        "date_format": DATE_FORMAT,
        "ema_data": True,
    },
    "1Y": {
        "timespan": "day",
        "before": lambda now: now - timedelta(days=365),
        "date_format": DATE_FORMAT,
        "ema_data": True,
    },
    "3Y": {
        "timespan": "week",
        "before": lambda now: now - timedelta(days=365*3),
        "date_format": DATE_FORMAT,
        "ema_data": False,
    },
    "5Y": {
        "timespan": "week",
        "before": lambda now: now - timedelta(days=365*5),
        "date_format": DATE_FORMAT,
        "ema_data": False,
    },
}

SELECT_DB_TABLE = {
    "minute": StockMinute,
    "hour": StockHour,
    "day": StockDay,
    "week": StockWeek,
}

# Timeframes for which we store the chart data in the database
DB_TIMEFRAMES = ["1D", "1W", "1Y", "5Y"]

def fetch_full_market_snapshot_data():
    full_market_snapshot_data = dict()

    # Getting "full market snapshot" endpoint data from polygon API
    try:
        snapshot = client.get_snapshot_all("stocks")
        metrics.increment(MetricName.MASSIVE_API_CALLS)
    except Exception as e:
        print(f"Error fetching snapshot data: {e}")
        snapshot = []

    for stock in snapshot:
        ticker = stock.ticker.upper() if stock else None
        if ticker and ticker not in full_market_snapshot_data:
            try:
                stock_data = {
                    "day_close": safe_getattr(stock.day, "close"),
                    "day_open": safe_getattr(stock.day, "open"),
                    "day_high": safe_getattr(stock.day, "high"),
                    "day_low": safe_getattr(stock.day, "low"),
                    "volume": safe_getattr(stock.day, "volume"),
                    "vwap": safe_getattr(stock.day, "vwap"),
                    "prev_o": safe_getattr(stock.prev_day, "open"),
                    "prev_h": safe_getattr(stock.prev_day, "high"),
                    "prev_l": safe_getattr(stock.prev_day, "low"),
                    "prev_c": safe_getattr(stock.prev_day, "close"),
                    "prev_v": safe_getattr(stock.prev_day, "volume"),
                    "prev_vwap": safe_getattr(stock.prev_day, "vwap"),
                    "todays_change": safe_getattr(stock, "todays_change"),
                    "todays_change_perc": safe_getattr(stock, "todays_change_percent"),
                    "last_updated": polygon_timestamp_to_utc_dt(stock.updated, "nanosecond")
                }

                # Check that all fields are not None
                if all(stock_data.get(attr) is not None for attr in FULL_MARKET_SNAPSHOT_ATTRIBUTES):
                    full_market_snapshot_data[ticker] = stock_data

            except Exception as e:
                print(f"Error processing stock {getattr(stock, 'ticker', 'UNKNOWN')}: {e}")

    print(f"Fetched {len(full_market_snapshot_data)} stocks for Full Market Snapshot!")
    return full_market_snapshot_data

def get_stock_master_data(full_market_snapshot_data, ticker_id_map, dataset_version_id):
    stock_master_data = []

    for ticker, stock_data in full_market_snapshot_data.items():
        try:
            data = stock_data.copy()
            data.update({
                "ticker_id": ticker_id_map.get(ticker, None),
                "dataset_version_id": dataset_version_id,
                "popularity": stock_data.get("day_close") * stock_data.get("volume")
            })

            # Check that all fields are not None
            if all(data.get(attr) is not None for attr in STOCK_MASTER_ATTRIBUTES):
                stock_master_data.append(data)

        except Exception as e:
            print(f"Error processing stock {ticker}: {e}")

    print(f"Number of Stock Master: {len(stock_master_data)}")
    return stock_master_data

def fetch_all_tickers_data():
    all_tickers_data = dict()

    # Getting "All Tickers" endpoint data from polygon API
    try:
        all_stocks = client.list_tickers(
            market="stocks", active="true", order="asc", limit="1000", sort="ticker"
        )
        metrics.increment(MetricName.MASSIVE_API_CALLS)
    except Exception as e:
        print(f"Error fetching all tickers data: {e}")
        all_stocks = []

    for stock in all_stocks:
        ticker = stock.ticker.upper() if stock else None
        if ticker and ticker not in all_tickers_data:
            try:
                stock_data = {
                    "name": stock.name,
                    "primary_exchange": stock.primary_exchange,
                    "stock_type_code": stock.type,
                }

                # Check that all fields are not None
                if all(stock_data.get(attr) is not None for attr in ALL_TICKERS_ATTRIBUTES):
                    all_tickers_data[ticker] = stock_data

            except Exception as e:
                print(f"Error processing stock {getattr(stock, 'ticker', 'UNKNOWN')}: {e}")

    print(f"Fetched {len(all_tickers_data)} stocks for All Tickers Data!")
    return all_tickers_data

def get_stock_detail_data(all_tickers_data, ticker_id_map, stock_type_id_map=None):
    def get_stock_type_id(stock_type_code):
        if stock_type_id_map:
            return stock_type_id_map.get(stock_type_code)
        else:
            return get_stock_type_id_by_code(stock_type_code)

    stock_detail_data = []

    for ticker, stock_data in all_tickers_data.items():
        try:
            updated_stock_data = {
                "ticker_id": ticker_id_map.get(ticker, None),
                "name": stock_data.get("name", None),
                "primary_exchange": stock_data.get("primary_exchange", None),
                "stock_type_id": get_stock_type_id(stock_data.get("stock_type_code", None)),
            }

            # Check that all fields are not None
            if all(updated_stock_data.get(attr) is not None for attr in STOCK_DETAIL_ATTRIBUTES):
                stock_detail_data.append(updated_stock_data)

        except Exception as e:
            print(f"Error processing stock {ticker}: {e}")

    print(f"Number of Stock Detail: {len(stock_detail_data)}")
    return stock_detail_data

def fetch_stock_types():
    stock_types = dict()
    try:
        stock_types = {
            t.code: t.description
            for t in client.get_ticker_types(asset_class="stocks", locale="us")
        }
        metrics.increment(MetricName.MASSIVE_API_CALLS)
    except Exception as e:
        print(f"Error while fetching stock types: {e}")

    print(f"Fetched {len(stock_types)} Stock Types!")
    return stock_types

def get_related_companies(ticker):
    try:
        related_companies = client.get_related_companies(ticker)
        metrics.increment(MetricName.MASSIVE_API_CALLS)
        return ",".join([company.ticker for company in related_companies])
    except:
        return None

def safe_getattr(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except:
        return default

def get_ticker_details(stock_data, ticker, now):
    try:
        details = client.get_ticker_details(ticker, date=now)
        metrics.increment(MetricName.MASSIVE_API_CALLS)

        stock_data["description"] = safe_getattr(details, "description", None)
        stock_data["homepage_url"] = safe_getattr(details, "homepage_url", None)
        stock_data["list_date"] = (
            datetime.strptime(details.list_date, DATE_FORMAT).date()
            if details.list_date else None
        )
        stock_data["industry"] = safe_getattr(details, "sic_description", None)
        stock_data["total_employees"] = safe_getattr(details, "total_employees", None)
        stock_data["market_cap"] = safe_getattr(details, "market_cap", None)

        stock_data["icon_url"] = safe_getattr(details.branding, "icon_url", None)

        stock_data["related_companies"] = get_related_companies(ticker)

    except Exception as e:
        print(f"[Details Error] {ticker}: {e}")
    return stock_data

def get_365_day_data(ticker, now, stock_master):
    now_dt = datetime.strptime(now, DATE_FORMAT)
    from_ = now_dt - timedelta(days=365)
    to = now_dt - timedelta(days=2)

    # Get the recent values from stock master
    data = {
        "open": [float(stock_master.day_open), float(stock_master.prev_o)],
        "high": [float(stock_master.day_high), float(stock_master.prev_h)],
        "low": [float(stock_master.day_low), float(stock_master.prev_l)],
        "close": [float(stock_master.day_close), float(stock_master.prev_c)],
        "volume": [int(stock_master.volume), int(stock_master.prev_v)]
    }

    for day_data in client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="day",
        from_=from_,
        to=to,
        adjusted=True,
        sort="desc",
        limit=365,
    ):
        data["open"].append(day_data.open)
        data["high"].append(day_data.high)
        data["low"].append(day_data.low)
        data["close"].append(day_data.close)
        data["volume"].append(int(day_data.volume))

    metrics.increment(MetricName.MASSIVE_API_CALLS)

    return data

def get_ticker_dmas(stock_data, stock_365_day_data):
    try:
        last_close = stock_365_day_data["close"][0]

        closing_200_days = stock_365_day_data["close"][:200]
        try:
            dma_200 = sum(closing_200_days) / len(closing_200_days)
        except ZeroDivisionError:
            dma_200 = None
        try:
            dma_200_perc_diff = (last_close - dma_200) / dma_200 * 100
        except ZeroDivisionError:
            dma_200_perc_diff = None

        closing_50_days = stock_365_day_data["close"][:50]
        try:
            dma_50 = sum(closing_50_days) / len(closing_50_days)
        except ZeroDivisionError:
            dma_50 = None
        try:
            dma_50_perc_diff = (last_close - dma_50) / dma_50 * 100
        except ZeroDivisionError:
            dma_50_perc_diff = None

        closing_30_days = stock_365_day_data["close"][:30]
        try:
            dma_30 = sum(closing_30_days) / len(closing_30_days)
        except ZeroDivisionError:
            dma_30 = None
        try:
            dma_30_perc_diff = (last_close - dma_30) / dma_30 * 100
        except ZeroDivisionError:
            dma_30_perc_diff = None

        stock_data["dma_200"] = dma_200
        stock_data["dma_50"] = dma_50
        stock_data["dma_30"] = dma_30

        stock_data["dma_200_perc_diff"] = dma_200_perc_diff
        stock_data["dma_50_perc_diff"] = dma_50_perc_diff
        stock_data["dma_30_perc_diff"] = dma_30_perc_diff
    except Exception as e:
        print(f"[DMA Error] {stock_data.get("ticker")}: {e}")
    return stock_data

def get_ticker_52w_hl(stock_data, stock_365_day_data):
    try:
        last_close = stock_365_day_data["close"][0]

        stock_data["high_52w"] = max(stock_365_day_data["high"]) if stock_365_day_data else None
        try:
            stock_data["high_52w_perc_diff"] = (stock_data["high_52w"] - last_close) / last_close * 100
        except ZeroDivisionError:
            stock_data["high_52w_perc_diff"] = None

        stock_data["low_52w"] = min(stock_365_day_data["low"]) if stock_365_day_data else None
        try:
            stock_data["low_52w_perc_diff"] = (stock_data["low_52w"] - last_close) / last_close * 100
        except ZeroDivisionError:
            stock_data["low_52w_perc_diff"] =None

    except Exception as e:
        print(f"[52W Error] {stock_data.get("ticker")}: {e}")
    return stock_data

def fetch_stock_data(stock_master=None, now=None):
    """
    For the given stock master of a stock, this function collects
    the data for all the attributes in 'STOCK_ATTRIBUTES' defined
    at the top of the script, using the polygon API. It then saves
    all this data as a Stock DB model object, and returns it.
    :param stock_master: StockMaster object associated with this Stock.
    :param now: The date for which we collect the data from polygon API.
    :return: Stock DB model object containing data for all attributes.
    """

    stock = None

    if not (stock_master and stock_master.ticker):
        return stock

    ticker = stock_master.ticker.symbol
    if not ticker:
        return stock

    if not now:
        now = db_last_updated_date()

    stock_data = {}
    stock_data = get_ticker_details(stock_data, ticker, now)

    stock_365_day_data = get_365_day_data(ticker, now, stock_master)
    stock_data = get_ticker_dmas(stock_data, stock_365_day_data)
    stock_data = get_ticker_52w_hl(stock_data, stock_365_day_data)

    for attribute in STOCK_ATTRIBUTES:
        if attribute not in stock_data:
            stock_data[attribute] = None
    stock = Stock(**stock_data)
    stock.stock_master_id = stock_master.id

    return stock

def fetch_chart_data(stock, timeframe, now=None):
    """
    Fetch chart data for a given stock object from Polygon API.
    The `stock` argument should be a Stock ORM object.
    """

    chart_data = []
    if not stock or not isinstance(stock, Stock):
        return chart_data

    if not (stock.stock_master and stock.stock_master.ticker):
        return chart_data

    ticker = stock.stock_master.ticker.symbol
    if not ticker:
        return chart_data

    last_updated = stock.stock_master.last_updated
    if not now:
        now = db_last_updated_date()

    timeframe_data = TIMEFRAME_OPTIONS[timeframe]
    timespan = timeframe_data.get("timespan")
    before = format_date(timeframe_data.get("before")(datetime.strptime(now, DATE_FORMAT)))
    db_table = SELECT_DB_TABLE.get(timespan)
    ema_data = timeframe_data.get("ema_data")

    common_timestamps = set()
    close_price_data = {}
    volume_data = {}

    # Price & volume
    for stock_data in client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan=timespan,
        from_=before,
        to=now,
        adjusted=True,
        sort="asc",
        limit=5000,
    ):
        timestamp = stock_data.timestamp
        common_timestamps.add(timestamp)
        close_price_data[timestamp] = stock_data.close
        volume_data[timestamp] = int(stock_data.volume)

    metrics.increment(MetricName.MASSIVE_API_CALLS)

    # EMA helper
    def get_ema_data(ema_window):
        ema_data_ = {}
        ema = client.get_ema(
            ticker=ticker,
            timestamp_gte=before,
            timespan=timespan,
            adjusted="true",
            window=ema_window,
            series_type="close",
            order="asc",
            limit="5000",
        )
        metrics.increment(MetricName.MASSIVE_API_CALLS)

        for value in ema.values:
            timestamp_ = value.timestamp
            ema_data_[timestamp_] = value.value
        return ema_data_

    # EMA calculations
    ema_30_data = {}
    ema_50_data = {}
    ema_200_data = {}
    if ema_data:
        ema_30_data = get_ema_data("30")
        ema_50_data = get_ema_data("50")
        ema_200_data = get_ema_data("200")

        common_timestamps &= set(ema_30_data) & set(ema_50_data) & set(ema_200_data)

    polygon_timestamp_type = "millisecond"
    last_updated_timestamp = utc_dt_to_polygon_timestamp(last_updated, polygon_timestamp_type)

    # Build ORM objects
    for timestamp in sorted(common_timestamps):
        # Only include the values upto the last updated timestamp
        if timestamp > last_updated_timestamp:
            break

        utc_date = polygon_timestamp_to_utc_dt(timestamp, polygon_timestamp_type)
        close_price = close_price_data[timestamp]
        volume = volume_data[timestamp]

        kwargs = dict(
            stock_id=stock.id,
            date=utc_date,
            close_price=close_price,
            volume=volume
        )

        if ema_data:
            kwargs.update(
                ema_30=ema_30_data[timestamp],
                ema_50=ema_50_data[timestamp],
                ema_200=ema_200_data[timestamp]
            )

        chart_data.append(db_table(**kwargs))

    return chart_data
