from app import app
from utils.db_queries.user_data import get_all_users, is_user_active, is_user_email_alert_on, user_has_watchlist_alerts
from utils.db_queries.watchlist import db_get_watchlist_alert_email_data
from watchlist.emails import WatchlistEmail

def send_watchlist_alert_emails():
    """
    Sends daily watchlist alert emails to users.
    Should be run after DB population is complete.
    """

    with app.app_context():
        # Get all the users
        users = get_all_users()

        print(f"\nSending watchlist alert emails to users...")

        # For each user
        num_users = 0
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

        print(f"\nWatchlist alert emails sent to {num_users} users.")
