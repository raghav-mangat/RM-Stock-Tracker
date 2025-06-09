import json
from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import os

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
# Connect to polygon API
client = RESTClient(POLYGON_API_KEY)

def get_all_tickers():
    """
    returns a set of all stock tickers in the etfs stored in etf_holdings.json.
    :return: set of all tickers.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # go one level up from scraper
    file_path = os.path.join(base_dir, "data", "etf_holdings.json")

    # Load ETF tickers
    with open(file_path) as f:
        etf_data = json.load(f)

    tickers = set()
    for etf in etf_data["etf_data"].values():
        for holding in etf["holdings"]:
            tickers.add(holding["ticker"])
    tickers.discard("")

    return tickers

def get_200_day_close_data(ticker):
    """
    uses the polygon API to return the close price of the given ticker
    for the past 200 days.
    :return: list of close prices for the past 200 days.
    """
    # Get the current date
    now = datetime.now()
    # Get the date 300 days from now
    now_300_days = now-timedelta(days=300)

    # Store the close data for past 200 days
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
    # return the data for the past 200 days
    return data_200_days[:200]

def fetch_and_save_stock_data():
    stock_data = {
        "info": {
        "last_updated": datetime.now().isoformat()
        },
        "stock_data": {}
    }

    # Set of all tickers present in the ETFs
    all_tickers = get_all_tickers()
    for ticker in all_tickers:
        try:
            print(f"Fetching data for {ticker}")
            # Closing price for the past 200 days
            closing_200_days = get_200_day_close_data(ticker)
            # Get last close
            last_close = closing_200_days[0]

            # Get 200-DMA
            dma_200 = sum(closing_200_days) / len(closing_200_days)

            stock_data["stock_data"][ticker] = {
                "last_close": round(last_close, 2),
                "dma_200": round(dma_200, 2),
                "perc_diff": round((last_close - dma_200) / dma_200 * 100, 2)
            }

        except Exception as e:
            print(f"Error for {ticker}: {e}")

    # Save to file
    base_dir = os.path.dirname(os.path.dirname(__file__))  # go one level up from scraper
    file_path = os.path.join(base_dir, "data", "stock_data.json")
    with open(file_path, "w") as f:
        json.dump(stock_data, f, indent=2)

    print("Stock data saved.")
