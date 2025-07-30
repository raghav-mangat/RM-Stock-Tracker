from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import os
from models.database import Stock, StockMaster, StockMinute, StockHour, StockDay
from utils.datetime_utils import polygon_timestamp_et, format_date, DATE_FORMAT, DATETIME_FORMAT
from utils.populate_db_info import db_last_updated_date

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
client = RESTClient(POLYGON_API_KEY)

# List of all attributes that we store in the database for all stocks available in Polygon API.
# Must be the same as all the fields in the Stock Master table in the database.
STOCK_MASTER_ATTRIBUTES = [
            "ticker", "name", "type", "primary_exchange", "last_updated", "day_close",
            "day_open", "day_high", "day_low", "volume", "todays_change", "todays_change_perc"
        ]

# List of all attributes that we store in the database for a given stock.
# Must be the same as all the fields in the Stock table in the database.
STOCK_ATTRIBUTES = [
            "name", "description", "homepage_url", "list_date", "industry", "type",
            "total_employees", "market_cap", "icon_url", "day_close", "day_open",
            "day_high", "day_low", "volume", "todays_change", "todays_change_perc",
            "dma_50", "dma_200", "dma_200_perc_diff", "high_52w", "low_52w",
            "related_companies", "last_updated"
        ]

TIMEFRAME_OPTIONS = {
    "1D": {
        "timespan": "minute",
        "before": lambda now: format_date(now),
        "date_format": DATETIME_FORMAT
    },
    "1W": {
        "timespan": "hour",
        "before": lambda now: format_date(now - timedelta(days=7)),
        "date_format": DATETIME_FORMAT
    },
    "1M": {
        "timespan": "day",
        "before": lambda now: format_date(now - timedelta(days=30)),
        "date_format": DATE_FORMAT
    },
    "3M": {
        "timespan": "day",
        "before": lambda now: format_date(now - timedelta(days=90)),
        "date_format": DATE_FORMAT
    },
    "6M": {
        "timespan": "day",
        "before": lambda now: format_date(now - timedelta(days=180)),
        "date_format": DATE_FORMAT
    },
    "YTD": {
        "timespan": "day",
        "before": lambda now: format_date(datetime(now.year, 1, 1)),
        "date_format": DATE_FORMAT
    },
    "1Y": {
        "timespan": "day",
        "before": lambda now: format_date(now - timedelta(days=365)),
        "date_format": DATE_FORMAT
    }
}

def fetch_all_stocks_data():
    """
    For all the stocks available in polygon API, this function collects
    the data for all the attributes in 'STOCK_MASTER_ATTRIBUTES' defined
    at the top of the script, using the polygon API. It then saves
    all this data as a list of Stock Master DB model objects, and returns it.
    :return: List of Stock Master DB model object, containing the required
        data for all the stocks available in polygon API
    """
    print("Retrieving data for all the stocks in polygon API...")
    stock_master_data = []

    # Get the ticker types
    try:
        ticker_types = {
            t.code: t.description for t in client.get_ticker_types(asset_class="stocks", locale="us")
        }
    except Exception as e:
        print(f"Error fetching ticker types: {e}")
        ticker_types = {}

    # Use the "All Tickers" endpoint in polygon API to get some data for each stock
    try:
        all_tickers_data = {
            t.ticker: {
                "name": t.name,
                "type": ticker_types.get(t.type),
                "primary_exchange": t.primary_exchange
            } for t in client.list_tickers(
                market="stocks", active="true", order="asc", limit="1000", sort="ticker"
            )
        }
    except Exception as e:
        print(f"Error fetching all tickers data: {e}")
        all_tickers_data = {}

    # Getting "full market snapshot" endpoint data from polygon API
    try:
        snapshot = client.get_snapshot_all("stocks")
    except Exception as e:
        print(f"Error fetching snapshot data: {e}")
        snapshot = []

    # For each stock in the snapshot, save all the required data for the stock
    # in a Stock Master DB model object, and add it to the list to be returned
    for stock in snapshot:
        try:
            ticker = stock.ticker
            ticker_meta = all_tickers_data.get(ticker)
            if not ticker_meta:
                raise ValueError("Missing metadata from all_tickers_data")

            stock_data = {
                "ticker": ticker,
                "name": ticker_meta["name"],
                "type": ticker_meta["type"],
                "primary_exchange": ticker_meta["primary_exchange"],
                "day_close": safe_getattr(stock.day, "close"),
                "day_open": safe_getattr(stock.day, "open"),
                "day_high": safe_getattr(stock.day, "high"),
                "day_low": safe_getattr(stock.day, "low"),
                "volume": safe_getattr(stock.day, "volume"),
                "todays_change": safe_getattr(stock, "todays_change"),
                "todays_change_perc": safe_getattr(stock, "todays_change_percent"),
                "last_updated": polygon_timestamp_et(stock.updated, "nanosecond")
            }

            # Check that all fields are not None
            if all(stock_data.get(attr) is not None for attr in STOCK_MASTER_ATTRIBUTES):
                stock_master_data.append(StockMaster(**stock_data))
            else:
                print(f"Skipping {ticker}: Incomplete data.")

        except Exception as e:
            print(f"Error processing stock {getattr(stock, 'ticker', 'UNKNOWN')}: {e}")

    print(f"Retrieved {len(stock_master_data)} stocks from Polygon API!")
    return stock_master_data

def get_ticker_type(ticker_type):
    try:
        types = client.get_ticker_types(asset_class="stocks", locale="us")
        for stock_type in types:
            if stock_type.code == ticker_type:
                return stock_type.description
    except:
        return None
    return None

def get_related_companies(ticker):
    try:
        related_companies = client.get_related_companies(ticker)
        return ",".join([company.ticker for company in related_companies])
    except:
        return None

def safe_getattr(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except:
        return default

def get_ticker_details(ticker, stock_data):
    try:
        details = client.get_ticker_details(ticker)

        stock_data["ticker"] = safe_getattr(details, "ticker", None)
        stock_data["icon_url"] = safe_getattr(details.branding, "icon_url", None)
        stock_data["description"] = safe_getattr(details, "description", None)
        stock_data["homepage_url"] = safe_getattr(details, "homepage_url", None)
        stock_data["list_date"] = (
            datetime.strptime(details.list_date, "%Y-%m-%d").date()
            if details.list_date else None
        )
        stock_data["name"] = safe_getattr(details, "name", None)
        stock_data["industry"] = safe_getattr(details, "sic_description", None)
        stock_data["total_employees"] = safe_getattr(details, "total_employees", None)
        stock_data["type"] = get_ticker_type(details.type)
        stock_data["related_companies"] = get_related_companies(ticker)
        stock_data["market_cap"] = safe_getattr(details, "market_cap", None)

    except Exception as e:
        print(f"[Details Error] {ticker}: {e}")
    return stock_data

def get_ticker_snapshot(ticker, stock_data):
    try:
        snapshot = client.get_snapshot_ticker("stocks", ticker)
        day = snapshot.day

        last_updated_timestamp = safe_getattr(snapshot, "updated", None)
        stock_data["last_updated"] = polygon_timestamp_et(last_updated_timestamp,"nanosecond")
        stock_data["day_high"] = safe_getattr(day, "high", None)
        stock_data["day_low"] = safe_getattr(day, "low", None)
        stock_data["day_close"] = safe_getattr(day, "close", None)
        stock_data["day_open"] = safe_getattr(day, "open", None)
        stock_data["volume"] = safe_getattr(day, "volume", None)
        stock_data["todays_change"] = round(safe_getattr(snapshot, "todays_change", 0), 2)
        stock_data["todays_change_perc"] = round(safe_getattr(snapshot, "todays_change_percent", 0), 2)

    except Exception as e:
        print(f"[Snapshot Error] {ticker}: {e}")
    return stock_data

def get_200_day_close_data(ticker):
    now = datetime.now()
    now_300_days = now - timedelta(days=300)
    data_200_days = []

    for day_data in client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="day",
        from_=now_300_days,
        to=now,
        adjusted=True,
        sort="desc",
        limit=200,
    ):
        data_200_days.append(day_data.close)

    return data_200_days[:200]

def get_ticker_dmas(ticker, stock_data):
    try:
        closing_200_days = get_200_day_close_data(ticker)
        if not closing_200_days:
            return stock_data

        last_close = closing_200_days[0]
        dma_200 = sum(closing_200_days) / len(closing_200_days)
        dma_200_perc_diff = (last_close - dma_200) / dma_200 * 100

        closing_50_days = closing_200_days[:50]
        dma_50 = sum(closing_50_days) / len(closing_50_days)

        stock_data["dma_200"] = round(dma_200, 2)
        stock_data["dma_50"] = round(dma_50, 2)
        stock_data["dma_200_perc_diff"] = round(dma_200_perc_diff, 2)
    except Exception as e:
        print(f"[DMA Error] {ticker}: {e}")
    return stock_data

def get_ticker_52w_hl(ticker, stock_data):
    try:
        now = datetime.now()
        now_365_days = now - timedelta(days=365)
        data_365_days_high = []
        data_365_days_low = []

        for day_data in client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=now_365_days,
            to=now,
            adjusted=True,
            sort="desc",
            limit=365,
        ):
            data_365_days_high.append(day_data.high)
            data_365_days_low.append(day_data.low)

        stock_data["high_52w"] = max(data_365_days_high) if data_365_days_high else None
        stock_data["low_52w"] = min(data_365_days_low) if data_365_days_low else None
    except Exception as e:
        print(f"[52W Error] {ticker}: {e}")
    return stock_data

def fetch_stock_data(ticker):
    """
    For the given ticker symbol of a stock, this function collects
    the data for all the attributes in 'STOCK_ATTRIBUTES' defined
    at the top of the script, using the polygon API. It then saves
    all this data as a Stock DB model object, and returns it.
    :param ticker: ticker symbol of a stock
    :return: Stock DB model object containing data for all attributes
    """
    stock = None
    stock_data = {}
    print(f"Fetching data for: {ticker}")

    stock_data = get_ticker_details(ticker, stock_data)
    stock_data = get_ticker_snapshot(ticker, stock_data)
    stock_data = get_ticker_dmas(ticker, stock_data)
    stock_data = get_ticker_52w_hl(ticker, stock_data)

    if stock_data.get("ticker"):
        for attribute in STOCK_ATTRIBUTES:
            if attribute not in stock_data:
                stock_data[attribute] = None
        stock = Stock(**stock_data)
    else:
        print(f"Skipping {ticker}: Ticker Symbol Missing.")

    return stock

def fetch_chart_data(stock_id, ticker, timeframe):
    now = db_last_updated_date()

    select_db_table = {
        "minute": StockMinute,
        "hour": StockHour,
        "day": StockDay
    }

    timeframe_data = TIMEFRAME_OPTIONS[timeframe]
    timespan = timeframe_data.get("timespan")
    before = timeframe_data.get("before")(datetime.strptime(now, DATE_FORMAT))
    db_table = select_db_table.get(timespan)

    close_price_data = {}
    volume_data = {}
    for day_data in client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan=timespan,
            from_=before,
            to=now,
            adjusted=True,
            sort="asc",
            limit=1000,
    ):
        timestamp = day_data.timestamp
        close_price_data[timestamp] = round(day_data.close, 2)
        volume_data[timestamp] = int(day_data.volume)

    def get_ema_data(ema_window):
        ema_data = {}
        ema = client.get_ema(
            ticker=ticker,
            timestamp_gte=before,
            timespan=timespan,
            adjusted="true",
            window=ema_window,
            series_type="close",
            order="asc",
            limit="1000",
        )
        for value in ema.values:
            timestamp_ = value.timestamp
            ema_data[timestamp_] = round(value.value, 2)
        return ema_data

    ema_30_data = get_ema_data("30")
    ema_50_data = get_ema_data("50")
    ema_200_data = get_ema_data("200")

    close_price_dates = set(close_price_data.keys())
    ema_30_dates = set(ema_30_data.keys())
    ema_50_dates = set(ema_50_data.keys())
    ema_200_dates = set(ema_200_data.keys())
    volume_dates = set(volume_data.keys())
    common_dates = close_price_dates.intersection(ema_30_dates).intersection(ema_50_dates).intersection(
        ema_200_dates).intersection(volume_dates)

    dates = list(sorted(common_dates))
    chart_data = []
    timestamp_type = "millisecond"
    for date in dates:
        et_date = polygon_timestamp_et(date, timestamp_type)

        close_price = close_price_data[date]
        ema_30 = ema_30_data[date]
        ema_50 = ema_50_data[date]
        ema_200 = ema_200_data[date]
        volume = volume_data[date]
        chart_data.append(db_table(
            stock_id=stock_id,
            date=et_date,
            close_price=close_price,
            ema_30=ema_30,
            ema_50=ema_50,
            ema_200=ema_200,
            volume=volume
        ))
    return chart_data
