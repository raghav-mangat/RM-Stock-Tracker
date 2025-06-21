from datetime import datetime, timedelta
import pytz
from polygon import RESTClient
from dotenv import load_dotenv
import os
from models.database import Stock

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
client = RESTClient(POLYGON_API_KEY)

# List of all attributes that we store in the database for a given stock.
# Must be the same as all the fields in the Stock table in the database.
stock_attributes = [
            "name", "description", "homepage_url", "list_date", "industry", "type",
            "total_employees", "market_cap", "icon_url", "last_close", "last_open",
            "day_high", "day_low", "volume", "todays_change", "todays_change_perc",
            "dma_50", "dma_200", "dma_200_perc_diff", "high_52w", "low_52w",
            "related_companies", "last_updated"
        ]

def get_all_stocks():
    print("Retrieving list of all stocks in polygon API...")
    stocks = []
    for t in client.list_tickers(
        market="stocks", active="true", order="asc", limit="1000", sort="ticker"
    ):
        stocks.append(t)
    print("Retrieved all stocks from polygon API!")
    return stocks

def convert_polygon_timestamp(nanosecond_timestamp):
    # Convert nanoseconds to seconds
    unix_seconds = nanosecond_timestamp / 1_000_000_000

    # Convert to UTC datetime
    utc_dt = datetime.fromtimestamp(unix_seconds, tz=pytz.utc)

    # Convert to US/Eastern timezone
    eastern_tz = pytz.timezone('US/Eastern')
    eastern_dt = utc_dt.astimezone(eastern_tz)

    return eastern_dt

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

        stock_data["icon_url"] = safe_getattr(details.branding, "icon_url", None)
        stock_data["description"] = safe_getattr(details, "description", None)
        stock_data["homepage_url"] = safe_getattr(details, "homepage_url", None)
        stock_data["list_date"] = (
            datetime.strptime(details.list_date, "%Y-%m-%d").date()
            if details.list_date else None
        )
        stock_data["name"] = safe_getattr(details, "name", None)
        stock_data["industry"] = safe_getattr(details, "sic_description", None)
        stock_data["ticker"] = safe_getattr(details, "ticker", None)
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

        updated_timestamp = safe_getattr(snapshot, "updated", None)
        stock_data["last_updated"] = convert_polygon_timestamp(updated_timestamp)
        stock_data["day_high"] = safe_getattr(day, "high", None)
        stock_data["day_low"] = safe_getattr(day, "low", None)
        stock_data["last_close"] = safe_getattr(day, "close", None)
        stock_data["last_open"] = safe_getattr(day, "open", None)
        stock_data["volume"] = safe_getattr(day, "volume", None)
        stock_data["todays_change"] = round(safe_getattr(snapshot, "todays_change", 0), 2)
        stock_data["todays_change_perc"] = round(safe_getattr(snapshot, "todays_change_percent", 0), 2)

    except Exception as e:
        print(f"[Snapshot Error] {ticker}: {e}")
    return stock_data

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
    stock_data = {}
    print(f"Fetching data for: {ticker}")

    stock_data = get_ticker_details(ticker, stock_data)
    stock_data = get_ticker_snapshot(ticker, stock_data)
    stock_data = get_ticker_dmas(ticker, stock_data)
    stock_data = get_ticker_52w_hl(ticker, stock_data)

    if not stock_data.get("ticker"):
        return None

    stock = Stock(**stock_data)
    return stock
