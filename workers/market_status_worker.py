import os
import sys

# Make sure that the project root is in Python's path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

from app import app
import time
import random
from data_collectors.market_data import fetch_market_status
from utils.status_files import write_to_status_file

def main():
    print("\nStarting Market Status Worker...")

    while True:
        try:
            with app.app_context():
                market_status = fetch_market_status()
                write_to_status_file("market_status.json", market_status)

            sleep_time = 60  # 1 minute

        except Exception as e:
            print(f"[Error] {e}")
            sleep_time = 60  # Fallback

        # Jitter (Important to avoid sync spikes)
        sleep_time += random.randint(0, 10)

        time.sleep(sleep_time)


if __name__ == "__main__":
    main()