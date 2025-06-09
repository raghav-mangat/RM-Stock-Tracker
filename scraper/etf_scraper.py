# Getting stock info of etfs

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os

def fetch_and_save_etf_data():
    # Define the ETFs and their URLs
    slick_charts_url = "https://www.slickcharts.com"
    etfs = {
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
            "name": "Berkshire Hathaway",
            "endpoint": f"{slick_charts_url}/berkshire-hathaway",
        },
        "ark-innovations": {
            "name": "Ark Innovation ETF",
            "endpoint": f"{slick_charts_url}/etf/ark-invest/ARKK",
        },
    }

    all_etf_data = {
        "info": {
            "last_updated": datetime.now().isoformat(),
            "etf_list": [key for key in etfs.keys()]
        },
        "etf_data": {}
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    for etf_name, etf_info in etfs.items():
        print(f"Scraping {etf_name}...")
        response = requests.get(etf_info.get("endpoint"), headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", class_="table")

        etf_holdings = []

        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 4:
                etf_holdings.append({
                    "rank": cols[0].text.strip(),
                    "name": cols[1].text.strip(),
                    "ticker": cols[2].text.strip(),
                    "weight": cols[3].text.strip()
                })

        all_etf_data["etf_data"][etf_name] = {
            "name": etf_info.get("name"),
            "holdings": etf_holdings
        }
        time.sleep(5)

    # Save to JSON file in the project
    base_dir = os.path.dirname(os.path.dirname(__file__))  # go one level up from scraper/
    file_path = os.path.join(base_dir, "data", "etf_holdings.json")

    with open(file_path, "w") as f:
        json.dump(all_etf_data, f, indent=2)

    print("✅ ETF holdings saved to data/etf_holdings.json")