import time
import requests
from bs4 import BeautifulSoup

# Define the indices and their URLs
slick_charts_url = "https://www.slickcharts.com"
indices_info = {
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
        "name": "Dow Jones Index",
        "slug": "dowjones",
        "url": f"{slick_charts_url}/dowjones",
    },
    "magnificent7": {
        "name": "Magnificent Seven Index",
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

# List of all indices available in this script
all_indices = list(indices_info.keys())

def get_index_info(index):
    """
    Returns the information for the index given to the function using the
    indices_info dict defined at the top of the script.
    :param index: key for a value in indices_info dict
    :return: dict of information for the given index
    """
    return indices_info.get(index)

def fetch_index_data(index):
    """
    Takes an index name for an index in slickcharts website, scrapes the website
    using beautiful soup, and returns a list of holdings for that index.
    Each element in the holdings list is a dict containing 'weight' and
    'ticker' symbol of each stock in the index.
    :param index: index name for an index is slickcharts website
    :return: index_holdings: List of dicts containing weight and ticker
    symbol for each stock in the index
    """

    url = None
    try:
        url = get_index_info(index).get("url")
    except AttributeError as e:
        print(f"[Index Error] Index <{index}> is invalid: {e}")

    print(f"Scraping: <{url}>...")
    # List of stock data dictionary for each stock in the index at the
    # given url
    index_holdings = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
    }

    # Getting response from the webpage at given url
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(5)
    except requests.RequestException as e:
        print(f"[Request Error] Failed to fetch {url}: {e}")
        return index_holdings

    try:
        # Create soup from the webpage response
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", class_="table")

        # Check if index data table exists in the soup
        if not table or not table.tbody:
            print(f"[Parse Error] Could not find table in {url}")
            return index_holdings

        # Retrieve stock data from the index data table
        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 4:
                ticker = cols[2].text.strip()
                weight = cols[3].text.strip().replace("%", "")
                index_holdings.append({
                    "ticker": ticker if ticker else None,
                    "weight": weight if weight else None,
                })

        return index_holdings

    except Exception as e:
        print(f"[Parsing Error] {url}: {e}")
        return []
