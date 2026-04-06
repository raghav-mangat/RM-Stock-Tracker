import requests
from bs4 import BeautifulSoup
import time
import random


def fetch_holdings_from_wikipedia(url, max_retries=3):
    holdings = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }

    for attempt in range(max_retries):
        try:
            # Small jitter before request
            time.sleep(random.uniform(2, 3))

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            table = soup.find("table", {"id": "constituents"})
            if not table:
                raise Exception("Constituents table not found")

            # ---- Extract header row ----
            header_row = table.find("tr")
            if not header_row:
                raise Exception("Header row not found")

            header_cells = header_row.find_all(["th", "td"])
            headers_text = [
                cell.get_text(strip=True).lower()
                for cell in header_cells
            ]

            # ---- Find ticker column ----
            ticker_col_index = None
            for i, col_name in enumerate(headers_text):
                if col_name in ["symbol", "ticker"]:
                    ticker_col_index = i
                    break

            if ticker_col_index is None:
                raise Exception("Ticker column not found")

            # ---- Parse data rows ----
            rows = table.find_all("tr")[1:]  # Skip header

            for row in rows:
                cols = row.find_all(["th", "td"])

                if not cols or len(cols) <= ticker_col_index:
                    continue

                ticker = cols[ticker_col_index].get_text(strip=True)

                if ticker:
                    holdings.append(ticker.strip().upper())

            if len(holdings) < 10:
                raise Exception("Too few holdings parsed")

            return holdings # Success -> Exit

        except Exception as e:
            print(f"[Retry {attempt + 1}] Failed {url}: {e}")
            time.sleep(1 + attempt)  # Simple Backoff

    return holdings  # Return empty if all retries fail


def fetch_sp500_holdings(url):
    return fetch_holdings_from_wikipedia(url)

def fetch_nasdaq100_holdings(url):
    return fetch_holdings_from_wikipedia(url)

def fetch_dow_jones_holdings(url):
    return fetch_holdings_from_wikipedia(url)

def fetch_magnificent7_holdings(url=None):
    holdings = ["GOOG", "AMZN", "AAPL", "META", "MSFT", "NVDA", "TSLA"]
    return holdings


# Define the indices available in this script and their info
indices_info = [
    {
        "slug": "sp500",
        "name": "S&P 500 Index",
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "fetch_func": fetch_sp500_holdings,
    },
    {
        "slug": "nasdaq100",
        "name": "Nasdaq 100 Index",
        "url": "https://en.wikipedia.org/wiki/Nasdaq-100",
        "fetch_func": fetch_nasdaq100_holdings,
    },
    {
        "slug": "dow-jones",
        "name": "Dow Jones Index",
        "url": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
        "fetch_func": fetch_dow_jones_holdings,
    },
    {
        "slug": "magnificent7",
        "name": "Magnificent Seven Index",
        "url": "https://en.wikipedia.org/wiki/Big_Tech#Magnificent_Seven",
        "fetch_func": fetch_magnificent7_holdings,
    },
]
