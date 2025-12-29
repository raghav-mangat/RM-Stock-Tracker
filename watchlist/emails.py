from flask import render_template
from utils.emails.email_service import EmailService

class WatchlistEmail(EmailService):

    @classmethod
    def watchlist_alert(cls, user, email_data):
        EmailService.enqueue_watchlist_email(
            subject="Watchlist Alert - RM Stock Tracker",
            recipients=[user.email],
            text_body=render_template(
                "email/watchlist_alert.txt",
                user=user,
                email_data=email_data
            ),
            html_body=render_template(
                "email/watchlist_alert.html",
                user=user,
                email_data=email_data
            )
        )
