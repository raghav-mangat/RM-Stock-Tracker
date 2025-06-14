# provides functions to access data from polygon api

from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import os

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
# Connect to polygon API
client = RESTClient(POLYGON_API_KEY)

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

def fetch_stock_data(ticker):
    stock_data = {}
    try:
        print(f"Fetching data for: {ticker}")

        # Get closing price for the past 200 days
        closing_200_days = get_200_day_close_data(ticker)
        # Get last close
        last_close = round(closing_200_days[0], 2)
        # Calculate 200-DMA
        dma_200 = round(sum(closing_200_days) / len(closing_200_days), 2)
        # Calculate percentage difference between last close and 200-DMA
        perc_diff = round((last_close - dma_200) / dma_200 * 100, 2)

        # Store the calculated data
        stock_data["last_close"] = last_close
        stock_data["dma_200"] = dma_200
        stock_data["perc_diff"] = perc_diff

        # Get the details of the stock
        details = client.get_ticker_details(
            ticker,
        )

        # Store name of the stock
        stock_data["name"] = details.name
        # Store ticker symbol of the stock
        stock_data["ticker"] = details.ticker
    except Exception as e:
        print(f"Error for {ticker}: {e}")

    return stock_data
