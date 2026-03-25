import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from utils.status_files import write_to_status_file, get_db_populate_status
from utils.datetime_utils import get_current_utc, format_dt_et, format_date_et, format_date
from utils.db_queries.user_data import get_all_users, is_user_active, is_user_email_alert_on, user_has_watchlist_alerts
from utils.db_queries.watchlist import db_get_watchlist_alert_email_data
from watchlist.emails import WatchlistEmail

def send_watchlist_alert_emails():
    """
    - Sends daily watchlist alert emails to users.
    - Should be run after DB population is complete.
    - We check if the db is populated on today's date and if
        so then it means the market was open and hence we send
        the emails.
    """

    # Number of users we sent the emails to
    num_users = 0

    with app.app_context():
        # Get all the users
        users = get_all_users()

        print(f"\nSending watchlist alert emails to users...")

        for user in users:
            # If all 3 conditions are satisfied for the user:
            # 1) User is active
            # 2) User has enabled email alerts
            # 3) User has any watchlist alerts
            if is_user_active(user) and is_user_email_alert_on(user) and user_has_watchlist_alerts(user):
                try:
                    # Get the email data for the user
                    email_data = db_get_watchlist_alert_email_data(user)

                    # If there is any email data
                    if email_data:
                        # Send watchlist alert email to the user
                        WatchlistEmail.watchlist_alert(
                            user=user,
                            email_data=email_data
                        )
                        num_users += 1

                except Exception:
                    print(f"Failed to send watchlist alert email to user: {user.id}")

        print(f"\nWatchlist alert emails sent to {num_users} users.\n")

    return num_users

def write_status(now, status):
    status_data = {
        "status": status,
        "last_send_attempted":  format_dt_et(now),
        "last_send_attempted_date": format_date_et(now)
    }

    if status == "success":
        status_data.update({
            "last_sent": format_dt_et(now),
            "last_sent_date": format_date_et(now)
        })

    with app.app_context():
        write_to_status_file(filename="sending_watchlist_email_alerts_status.json", status_data=status_data)

def main():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "send_watchlist_email_alerts"}
    )

    now = get_current_utc()
    now_date = format_date(now)

    write_status(now, status="running")

    try:
        with app.app_context():
            db_populate_status = get_db_populate_status()
            db_last_updated_date = db_populate_status.get("last_updated_date", "") if db_populate_status else ""

        if db_last_updated_date:
            message = f"\nDB populate last updated date: {db_last_updated_date}, Now date: {now_date}"
            if db_last_updated_date != now_date:
                print(f"{message} - Skipping!")
                write_status(now, status="skipped")
                app.logger.info(
                    f"Skipping script",
                    extra={"log_type": "scheduled_script", "action": "send_watchlist_email_alerts",
                           "reason": message}
                )
            else:
                print(f"{message} - Proceeding!")

                num_users = send_watchlist_alert_emails()
                write_status(now, status="success")

                app.logger.info(
                    f"Completed script, emails sent to {num_users or 0} users",
                    extra={"log_type": "scheduled_script", "action": "send_watchlist_email_alerts"}
                )
        else:
            message = "\nDB populate status missing - Cannot determine whether to proceed!"
            print(message)
            raise Exception(message)

    except Exception as e:
        write_status(now, status="failed")
        app.logger.exception(
            f"Script failed",
            extra={"log_type": "scheduled_script", "action": "send_watchlist_email_alerts", "reason": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
