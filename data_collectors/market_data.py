from polygon import RESTClient
import os
import time
from dotenv import load_dotenv
from metrics import metrics
from metrics.registry import MetricName
from utils.datetime_utils import get_current_utc

load_dotenv()
client = RESTClient(os.getenv("POLYGON_API_KEY"))

def fetch_market_status(retries=3):
    for attempt in range(retries):
        try:
            # Get market status from polygon API
            result = client.get_market_status()
            metrics.increment(MetricName.MASSIVE_API_CALLS)

            return {
                "market": result.market,
                "server_time": result.server_time,
                "timestamp": get_current_utc().isoformat()
            }

        except Exception as e:
            print(f"[Retry {attempt+1}] Error: {e}")
            time.sleep(1 + attempt)

    raise Exception("Failed to fetch market status after retries")
