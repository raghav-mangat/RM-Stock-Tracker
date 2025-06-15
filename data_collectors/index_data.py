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
        "slug": "dowjones",
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
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(5)
    except requests.RequestException as e:
        print(f"[Request Error] Failed to fetch {url}: {e}")
        return []

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", class_="table")

        if not table or not table.tbody:
            print(f"[Parse Error] Could not find table in {url}")
            return []

        index_holdings = []

        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 4:
                ticker = cols[2].text.strip()
                weight = cols[3].text.strip().replace("%", "")
                index_holdings.append({
                    "ticker": ticker if ticker else "N/A",
                    "weight": weight if weight else None,
                })

        return index_holdings

    except Exception as e:
        print(f"[Parsing Error] {url}: {e}")
        return []
