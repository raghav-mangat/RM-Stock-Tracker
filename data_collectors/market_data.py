import json
from pathlib import Path
from polygon import RESTClient
from dotenv import load_dotenv
import os

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
client = RESTClient(POLYGON_API_KEY)

# Define file path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "market_status.json"

# Ensure folder exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Get market status from polygon API
result = client.get_market_status()
market_status = result.market
server_time = result.server_time

# Prepare data
status_data = {
    "market_status": market_status,
    "server_time": server_time
}

# Save to JSON
with open(DATA_FILE, "w") as f:
    json.dump(status_data, f, indent=2)

print(f"Market status saved!\nMarket Status was {market_status} at {server_time}")
