import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from data_collectors.index_data import indices_info
from utils.data_files import write_to_data_file, read_data_file
from utils.datetime_utils import get_current_utc

DATA_FILE_NAME = "indices_data.json"


def main():
    with app.app_context():
        app.logger.info(
            "Starting script",
            extra={"log_type": "scheduled_script", "action": "store_indices_data"}
        )

        try:
            now = get_current_utc().isoformat()

            existing_indices_data = read_data_file(DATA_FILE_NAME) or dict()
            existing_indices_data = existing_indices_data.get("indices", dict())

            new_indices_data = dict()

            for index_info in indices_info:
                try:
                    slug = index_info.get("slug", "")
                    name = index_info.get("name", "")
                    url = index_info.get("url", "")
                    holdings = []

                    print(f"Fetching holdings for {slug}...")
                    fetch_func = index_info.get("fetch_func", None)
                    if fetch_func:
                        holdings = fetch_func(url)
                    print(f"Fetched holdings for {slug}!")

                    if holdings:
                        new_indices_data[slug] = {
                            "slug": slug,
                            "name": name,
                            "url": url,
                            "updated_at": now,
                            "holdings_count": len(holdings),
                            "holdings": holdings,
                        }
                    else:
                        new_indices_data[slug] = existing_indices_data.get(slug, dict())

                except Exception as e:
                    app.logger.exception(
                        f"Failed to fetch index: {slug}",
                        extra={
                            "log_type": "scheduled_script",
                            "action": "store_indices_data",
                            "reason": str(e),
                        }
                    )
                    continue

            # Final data structure
            final_data = {
                "updated_at": now,
                "indices": new_indices_data,
            }

            # Write to JSON (atomic)
            write_to_data_file(DATA_FILE_NAME, final_data)

            app.logger.info(
                "Completed script",
                extra={
                    "log_type": "scheduled_script",
                    "action": "store_indices_data"
                }
            )

        except Exception as e:
            app.logger.exception(
                "Script failed",
                extra={
                    "log_type": "scheduled_script",
                    "action": "store_indices_data",
                    "reason": str(e),
                }
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
