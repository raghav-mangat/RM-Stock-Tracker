import sys
from polygon import RESTClient
from dotenv import load_dotenv
import os
from app import app
from scheduled_scripts.helpers.helpers import write_to_status_file
from utils.datetime_utils import get_current_utc, format_dt_et, format_date


def main():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "store_market_status"}
    )

    now = get_current_utc()
    filename = "market_status.json"
    status_data = {
        "last_update_attempted": format_dt_et(now),
        "last_update_attempted_date": format_date(now)
    }

    try:
        load_dotenv()
        client = RESTClient(os.getenv("POLYGON_API_KEY"))

        # Get market status from polygon API
        result = client.get_market_status()
        market_status = result.market
        server_time = result.server_time

        # Prepare data
        status_data.update({
            "market_status": market_status,
            "server_time": server_time,
            "last_updated": format_dt_et(now),
            "last_updated_date": format_date(now)
        })

        write_to_status_file(filename, status_data)

        print(f"Market Status Saved!\nMarket Status was <{market_status}> at <{server_time}>")
        app.logger.info(
            f"Completed script",
            extra={"log_type": "scheduled_script", "action": "store_market_status"}
        )

    except Exception as e:
        write_to_status_file(filename, status_data)
        app.logger.exception(
            f"Script failed",
            extra={"log_type": "scheduled_script", "action": "store_market_status", "reason": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()