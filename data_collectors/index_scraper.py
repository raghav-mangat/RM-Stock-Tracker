# Getting stock info of indexes

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os

def fetch_and_save_index_data():
    # Define the indexes and their URLs
    slick_charts_url = "https://www.slickcharts.com"
    indexes = {
        "sp500": {
            "name": "S&P 500 Index",
            "endpoint": f"{slick_charts_url}/sp500",
        },
        "nasdaq100": {
            "name": "Nasdaq 100 Index",
            "endpoint": f"{slick_charts_url}/nasdaq100",
        },
        "dowjones": {
            "name": "Dow Jones",
            "endpoint": f"{slick_charts_url}/dowjones",
        },
        "magnificent7": {
            "name": "Magnificent Seven",
            "endpoint": f"{slick_charts_url}/magnificent7",
        },
        "berkshire-hathaway": {
            "name": "Berkshire Hathaway Holdings",
            "endpoint": f"{slick_charts_url}/berkshire-hathaway",
        },
        "ark-innovations": {
            "name": "Ark Innovation Index",
            "endpoint": f"{slick_charts_url}/etf/ark-invest/ARKK",
        },
    }

    all_index_data = {
        "info": {
            "last_updated": datetime.now().isoformat(),
            "index_list": [key for key in indexes.keys()]
        },
        "index_data": {}
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    for index_name, index_info in indexes.items():
        print(f"Scraping {index_name}...")
        response = requests.get(index_info.get("endpoint"), headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", class_="table")

        index_holdings = []

        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 4:
                index_holdings.append({
                    "rank": cols[0].text.strip(),
                    "name": cols[1].text.strip(),
                    "ticker": cols[2].text.strip(),
                    "weight": cols[3].text.strip()
                })

        all_index_data["index_data"][index_name] = {
            "name": index_info.get("name"),
            "holdings": index_holdings
        }
        time.sleep(5)

    # Save to JSON file in the project
    folder_name = "data"
    file_name = "index_holdings.json"
    base_dir = os.path.dirname(os.path.dirname(__file__))  # go one level up from scraper
    file_path = os.path.join(base_dir, folder_name, file_name)

    # Create 'data/' folder if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(all_index_data, f, indent=2)

    print(f"Index holdings saved to {folder_name}/{file_name}")
