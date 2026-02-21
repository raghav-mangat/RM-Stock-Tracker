import sys
from helpers.helpers import write_to_status_file
from app import app

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