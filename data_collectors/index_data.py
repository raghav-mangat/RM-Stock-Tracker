# Getting stock info of indexes

import time
import requests
from bs4 import BeautifulSoup

# Define the indexes and their URLs
slick_charts_url = "https://www.slickcharts.com"
indexes = {
    "sp500": {
        "name": "S&P 500 Index",
        "slug": "sp500",
        "url": f"{slick_charts_url}/sp500",
    },
    "nasdaq100": {
        "name": "Nasdaq 100 Index",
        "slug": "nasdaq100",
        "url": f"{slick_charts_url}/nasdaq100",
    },
    "dowjones": {
        "name": "Dow Jones",
        "slug": "dowjones" ,
        "url": f"{slick_charts_url}/dowjones",
    },
    "magnificent7": {
        "name": "Magnificent Seven",
        "slug": "magnificent7",
        "url": f"{slick_charts_url}/magnificent7",
    },
    "berkshire-hathaway": {
        "name": "Berkshire Hathaway Holdings",
        "slug": "berkshire-hathaway",
        "url": f"{slick_charts_url}/berkshire-hathaway",
    },
    "ark-innovations": {
        "name": "Ark Innovation Index",
        "slug": "ARKK",
        "url": f"{slick_charts_url}/etf/ark-invest/ARKK",
    },
}

def fetch_index_data(url):
    print(f"Scraping: <{url}>...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }
    response = requests.get(url=url, headers=headers)
    time.sleep(5)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", class_="table")

    index_holdings = []

    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 4:
            ticker = cols[2].text.strip()
            if ticker == "":
                ticker = "N/A"
            index_holdings.append({
                "rank": cols[0].text.strip(),
                "ticker": ticker,
                "weight": cols[3].text.strip().replace("%", "")
            })

    return index_holdings
