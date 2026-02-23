import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from helpers.helpers import write_to_status_file

def main():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "clear_db_last_updated_date"}
    )

    try:
        status_data = {
            "last_updated_date": ""
        }
        write_to_status_file(filename="populate_db_info.json", status_data=status_data)

        app.logger.info(
            f"Completed script",
            extra={"log_type": "scheduled_script", "action": "clear_db_last_updated_date"}
        )

    except Exception as e:
        app.logger.exception(
            f"Script failed",
            extra={"log_type": "scheduled_script", "action": "clear_db_last_updated_date", "reason": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()