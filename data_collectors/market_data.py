from polygon import RESTClient
import os

client = RESTClient(os.getenv("POLYGON_API_KEY"))

def fetch_market_data():
    # Get market status from polygon API
    result = client.get_market_status()

    return {
        "market_status": result.market,
        "server_time": result.server_time
    }